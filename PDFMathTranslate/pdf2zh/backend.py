from flask import Flask, request, send_file, jsonify, make_response
from celery import Celery, Task
from celery.result import AsyncResult
from pdf2zh import translate_stream
import tqdm
import json
import io
import secrets
import sqlite3
import os
from pathlib import Path
from functools import wraps
from pdf2zh.doclayout import ModelInstance
from pdf2zh.config import ConfigManager

flask_app = Flask("pdf2zh")
flask_app.config.from_mapping(
    CELERY=dict(
        broker_url=ConfigManager.get("CELERY_BROKER", "redis://127.0.0.1:6379/0"),
        result_backend=ConfigManager.get("CELERY_RESULT", "redis://127.0.0.1:6379/0"),
    )
)

# 数据库路径与配置文件在同一目录
DB_PATH = Path.home() / ".config" / "PDFMathTranslate" / "tasks.db"

def init_db():
    """初始化数据库"""
    # 确保目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS task_ownership
        (task_id TEXT PRIMARY KEY, user_token TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

def store_task_ownership(task_id: str, user_token: str):
    """存储任务所有权信息到数据库"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO task_ownership (task_id, user_token) VALUES (?, ?)',
              (task_id, user_token))
    conn.commit()
    conn.close()

def get_task_ownership(task_id: str) -> str:
    """从数据库获取任务所有权信息"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT user_token FROM task_ownership WHERE task_id = ?', (task_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def check_task_ownership(task_id):
    """检查当前用户是否拥有此任务的访问权限"""
    user_token = request.cookies.get('user_token')
    if not user_token:
        return False
    stored_token = get_task_ownership(task_id)
    return stored_token and stored_token == user_token

def require_ownership(f):
    """装饰器：要求用户拥有任务的访问权限"""
    @wraps(f)
    def decorated_function(id, *args, **kwargs):
        if not check_task_ownership(id):
            return jsonify({"error": "Unauthorized access"}), 403
        return f(id, *args, **kwargs)
    return decorated_function


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.Task = FlaskTask
    celery_app.set_default()
    celery_app.autodiscover_tasks()
    app.extensions["celery"] = celery_app
    return celery_app


celery_app = celery_init_app(flask_app)


@celery_app.task(bind=True)
def translate_task(
    self: Task,
    stream: bytes,
    args: dict,
):
    def progress_bar(t: tqdm.tqdm):
        self.update_state(state="PROGRESS", meta={"n": t.n, "total": t.total})  # noqa
        print(f"Translating {t.n} / {t.total} pages")

    doc_mono, doc_dual = translate_stream(
        stream,
        callback=progress_bar,
        model=ModelInstance.value,
        **args,
    )
    return doc_mono, doc_dual


def mask_sensitive_info(config):
    """对敏感信息进行脱敏处理"""
    masked = config.copy()
    for key in masked:
        if any(sensitive in key.upper() for sensitive in ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
            if masked[key]:
                # 保留前3位和后3位,中间用*号代替
                value = str(masked[key])
                if len(value) > 8:
                    masked[key] = value[:3] + '*' * (len(value)-6) + value[-3:]
                else:
                    masked[key] = '******'
    return masked


@flask_app.route("/v1/translate", methods=["POST"])
def create_translate_tasks():
    file = request.files["file"]
    stream = file.stream.read()
    print(request.form.get("data"))
    args = json.loads(request.form.get("data"))
    
    # 从cookie获取完整配置
    translator_config = get_translator_config_from_cookie()
    if translator_config:
        args["translator_config"] = translator_config
        
    task = translate_task.delay(stream, args)
    
    # 生成用户token并存储任务所有权
    user_token = request.cookies.get('user_token')
    if not user_token:
        user_token = secrets.token_urlsafe(32)
    
    # 存储到数据库
    store_task_ownership(task.id, user_token)
    
    # 创建响应
    response = jsonify({"id": task.id})
    
    # 设置cookie
    if not request.cookies.get('user_token'):
        response.set_cookie('user_token', user_token, httponly=True, samesite='Strict')
    
    return response


@flask_app.route("/v1/translate/<id>", methods=["GET"])
@require_ownership
def get_translate_task(id: str):
    result: AsyncResult = celery_app.AsyncResult(id)
    if str(result.state) == "PROGRESS":
        return {"state": str(result.state), "info": result.info}
    else:
        return {"state": str(result.state)}


@flask_app.route("/v1/translate/<id>", methods=["DELETE"])
@require_ownership
def delete_translate_task(id: str):
    result: AsyncResult = celery_app.AsyncResult(id)
    result.revoke(terminate=True)
    return {"state": str(result.state)}


@flask_app.route("/v1/translate/<id>/<format>")
@require_ownership
def get_translate_result(id: str, format: str):
    result = celery_app.AsyncResult(id)
    if not result.ready():
        return {"error": "task not finished"}, 400
    if not result.successful():
        return {"error": "task failed"}, 400
    doc_mono, doc_dual = result.get()
    to_send = doc_mono if format == "mono" else doc_dual
    return send_file(io.BytesIO(to_send), "application/pdf")


@flask_app.route("/v1/translator/config/masked", methods=["GET"])
def get_masked_translator_config():
    """获取脱敏后的翻译器配置"""
    config = get_translator_config_from_cookie()
    if not config:
        return jsonify({"error": "No configuration found"}), 404
    
    return jsonify(mask_sensitive_info(config))


if __name__ == "__main__":
    flask_app.run()
