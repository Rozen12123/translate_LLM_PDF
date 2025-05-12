import http.server
import socketserver
import os
import uuid
import json
import io
import cgi
import logging
import threading
import queue
from urllib.parse import parse_qs, urlparse
from pathlib import Path

# Import the DeepSeek translator
from deepseek_translator import DeepSeekTranslator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure directories
UPLOAD_FOLDER = Path('./uploads')
RESULT_FOLDER = Path('./results')
STATIC_FOLDER = Path('./static')

# Create directories if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULT_FOLDER.mkdir(exist_ok=True)
STATIC_FOLDER.mkdir(exist_ok=True)

# Task queue for translation jobs
job_queue = queue.Queue()
job_results = {}
job_statuses = {}

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def translation_worker():
    """Worker thread to process translation tasks"""
    translator = None
    
    while True:
        try:
            job_id, input_path, output_path, model_type = job_queue.get()
            
            try:
                job_statuses[job_id] = "processing"
                
                # Initialize translator if needed
                if not translator or translator.model_type != model_type:
                    translator = DeepSeekTranslator(model_type=model_type)
                
                # Translate the PDF
                success = translator.translate_pdf(input_path, output_path)
                
                # Update job status
                if success:
                    job_statuses[job_id] = "completed"
                    job_results[job_id] = {
                        "output_filename": os.path.basename(output_path)
                    }
                else:
                    job_statuses[job_id] = "failed"
                    job_results[job_id] = {
                        "error": "Translation failed. Check logs for details."
                    }
                
            except Exception as e:
                logger.error(f"Translation error (Job {job_id}): {str(e)}")
                job_statuses[job_id] = "failed"
                job_results[job_id] = {
                    "error": str(e)
                }
        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}")
        finally:
            job_queue.task_done()

# Start worker thread
worker_thread = threading.Thread(target=translation_worker, daemon=True)
worker_thread.start()

# Generate HTML content
def generate_index_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>审计报告翻译工具 | Audit Report Translator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
            }
            .upload-form {
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .btn {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .btn:hover {
                background-color: #2980b9;
            }
            footer {
                text-align: center;
                margin-top: 20px;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>审计报告翻译工具 | Audit Report Translator</h1>
            
            <div class="upload-form">
                <h2>上传报告 | Upload Report</h2>
                <p>请选择要翻译的中文审计报告PDF文件。</p>
                <p>Please select a Chinese audit report PDF file to translate.</p>
                
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <div>
                        <input type="file" id="file" name="file" accept=".pdf" required>
                    </div>
                    <div style="margin-top: 10px;">
                        <label for="model_type">翻译模型 | Translation Model:</label>
                        <select id="model_type" name="model_type">
                            <option value="standard">标准模型 | Standard Model</option>
                            <option value="professional">专业模型 | Professional Model</option>
                            <option value="enhanced">增强模型 | Enhanced Model</option>
                        </select>
                    </div>
                    <button type="submit" class="btn" style="margin-top: 10px;">
                        上传并翻译 | Upload and Translate
                    </button>
                </form>
            </div>
            
            <div>
                <h2>关于 | About</h2>
                <p>此工具设计用于将中文审计报告准确翻译成英文，同时保持原始格式。</p>
                <p>This tool is designed to accurately translate Chinese audit reports to English while preserving the original formatting.</p>
                <p>此为测试版本，上传文件有泄露风险，谨慎使用</p>
                <p>此为测试版本，上传文件有泄露风险，谨慎使用</p>
            </div>
            
            <footer>
                © 2025 Audit Report Translation Tool
            </footer>
        </div>
    </body>
    </html>
    """

def generate_progress_html(job_id, status):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>翻译进度 | Translation Progress</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
            }}
            .progress-container {{
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }}
            .btn {{
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                display: inline-block;
                text-decoration: none;
            }}
            .btn:hover {{
                background-color: #2980b9;
            }}
            footer {{
                text-align: center;
                margin-top: 20px;
                color: #7f8c8d;
            }}
            #status {{
                font-weight: bold;
                margin: 20px 0;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .hidden {{
                display: none;
            }}
        </style>
        <script>
            function checkStatus() {{
                fetch('/status?job_id={job_id}')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('status').textContent = '状态 Status: ' + data.status;
                        
                        if (data.status === 'completed') {{
                            document.getElementById('spinner').classList.add('hidden');
                            document.getElementById('success').classList.remove('hidden');
                            document.getElementById('download-btn').classList.remove('hidden');
                            document.getElementById('download-btn').href = '/download?filename=' + data.output_filename;
                        }} else if (data.status === 'failed') {{
                            document.getElementById('spinner').classList.add('hidden');
                            document.getElementById('error').classList.remove('hidden');
                            document.getElementById('error-details').textContent = data.error || 'Unknown error';
                        }} else {{
                            // Still processing, check again in 2 seconds
                            setTimeout(checkStatus, 2000);
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error checking status:', error);
                        document.getElementById('status').textContent = 'Error checking status';
                    }});
            }}
            
            window.onload = function() {{
                checkStatus();
            }};
        </script>
    </head>
    <body>
        <div class="container">
            <h1>翻译进度 | Translation Progress</h1>
            
            <div class="progress-container">
                <h2>翻译任务状态 | Translation Task Status</h2>
                <p>任务ID | Job ID: {job_id}</p>
                <p id="status">状态 Status: {status}</p>
                
                <div id="spinner" class="spinner"></div>
                
                <div id="success" class="hidden">
                    <p style="color: green;">✓ 翻译完成！Translation completed successfully!</p>
                </div>
                
                <div id="error" class="hidden">
                    <p style="color: red;">✗ 翻译失败 Translation failed</p>
                    <p id="error-details"></p>
                </div>
                
                <a id="download-btn" href="#" class="btn hidden">下载翻译文件 Download Translated File</a>
                
                <p style="margin-top: 20px;">
                    <a href="/" class="btn">返回首页 Back to Home</a>
                </p>
            </div>
            
            <footer>
                © 2025 Audit Report Translation Tool
            </footer>
        </div>
    </body>
    </html>
    """

def generate_error_html(message):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>错误 | Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #e74c3c;
                text-align: center;
            }}
            .error-container {{
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #e74c3c;
                border-radius: 5px;
                background-color: #fadbd8;
            }}
            .btn {{
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                display: inline-block;
                text-decoration: none;
            }}
            .btn:hover {{
                background-color: #2980b9;
            }}
            footer {{
                text-align: center;
                margin-top: 20px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>错误 | Error</h1>
            
            <div class="error-container">
                <p>{message}</p>
            </div>
            
            <div style="text-align: center;">
                <a href="/" class="btn">返回首页 Back to Home</a>
            </div>
            
            <footer>
                © 2025 Audit Report Translation Tool
            </footer>
        </div>
    </body>
    </html>
    """

class TranslationServer(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the translation service"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        
        if path == '/' or path == '':
            # Serve index page
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_index_html().encode('utf-8'))
            
        elif path == '/progress':
            # Show progress page
            if 'job_id' in query and query['job_id'][0] in job_statuses:
                job_id = query['job_id'][0]
                status = job_statuses[job_id]
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(generate_progress_html(job_id, status).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(generate_error_html("无效的任务ID | Invalid job ID").encode('utf-8'))
                
        elif path == '/status':
            # Return status as JSON
            if 'job_id' in query and query['job_id'][0] in job_statuses:
                job_id = query['job_id'][0]
                status = job_statuses[job_id]
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if status == "completed":
                    result = {
                        'status': status,
                        'output_filename': job_results[job_id]['output_filename']
                    }
                elif status == "failed":
                    result = {
                        'status': status,
                        'error': job_results[job_id].get('error', 'Unknown error')
                    }
                else:
                    result = {'status': status}
                
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'not_found'}).encode('utf-8'))
                
        elif path == '/download':
            # Download translated file
            if 'filename' in query:
                filename = query['filename'][0]
                file_path = os.path.join(RESULT_FOLDER, filename)
                
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/pdf')
                        # 使用ASCII兼容的编码来处理文件名
                        encoded_filename = filename.encode('utf-8').decode('latin-1')
                        self.send_header('Content-Disposition', f'attachment; filename="{encoded_filename}"')
                        self.end_headers()
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(generate_error_html("文件未找到 | File not found").encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(generate_error_html("未指定文件名 | No filename specified").encode('utf-8'))
                
        else:
            # Try to serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/upload':
            # Handle file upload
            content_type, pdict = cgi.parse_header(self.headers['content-type'])
            
            if content_type == 'multipart/form-data':
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': self.headers['Content-Type']}
                )
                
                # Check if file was uploaded
                if 'file' in form:
                    fileitem = form['file']
                    
                    # Check if file field was empty
                    if fileitem.filename:
                        # Check if file type is allowed
                        if allowed_file(fileitem.filename):
                            # Generate unique job ID
                            job_id = str(uuid.uuid4())
                            
                            # Get original filename and create a clean version for storage
                            original_filename = fileitem.filename
                            
                            # Store with job_id prefix for tracking
                            storage_filename = f"{job_id}_{original_filename}"
                            file_path = os.path.join(UPLOAD_FOLDER, storage_filename)
                            
                            # Save uploaded file
                            with open(file_path, 'wb') as f:
                                f.write(fileitem.file.read())
                            
                            # Get translation model preference
                            model_type = form.getvalue('model_type', 'standard')
                            
                            # Generate user-friendly output filename
                            name_base, ext = os.path.splitext(original_filename)
                            output_filename = f"{name_base}-英文版{ext}"
                            output_path = os.path.join(RESULT_FOLDER, output_filename)
                            
                            # Add task to queue
                            job_statuses[job_id] = "queued"
                            job_queue.put((job_id, file_path, output_path, model_type))
                            
                            # Redirect to progress page
                            self.send_response(302)
                            self.send_header('Location', f'/progress?job_id={job_id}')
                            self.end_headers()
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            self.wfile.write(generate_error_html("文件类型无效。只允许PDF文件。 | Invalid file type. Only PDF files are allowed.").encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(generate_error_html("未选择文件 | No selected file").encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(generate_error_html("没有选择文件 | No file part").encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(generate_error_html("无效的请求内容类型 | Invalid request content type").encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_error_html("找不到请求的资源 | Resource not found").encode('utf-8'))

# Start the server
def main():
    port = 5001
    server = socketserver.TCPServer(("", port), TranslationServer)
    
    print(f"启动审计报告翻译工具服务器，请访问: http://localhost:{port}")
    print(f"Starting Audit Report Translation Tool server at: http://localhost:{port}")
    print("按 Ctrl+C 停止服务器 | Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止 | Server stopped")
        server.server_close()

if __name__ == "__main__":
    main() 