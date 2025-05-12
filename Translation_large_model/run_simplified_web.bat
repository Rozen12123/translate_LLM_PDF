@echo off
echo 正在启动审计报告翻译工具简易网页版...
echo Starting Simplified Audit Report Translator Web Application...

REM 检查是否安装了必要的依赖项
python -c "import PyPDF2, reportlab, requests, tqdm" > nul 2>&1
if errorlevel 1 (
    echo 错误: 缺少必要的依赖项。
    echo Error: Missing required dependencies.
    echo.
    echo 请先运行 install_dependencies.bat 或手动安装依赖项:
    echo Please run install_dependencies.bat or manually install dependencies:
    echo pip install PyPDF2 reportlab requests tqdm
    echo.
    pause
    exit /b 1
)

python simplified_web_app.py
if errorlevel 1 (
    echo 启动应用时出错。请查看上面的错误信息。
    echo Error starting application. Please check the error message above.
    echo.
    echo 如果遇到模块缺失错误，请运行: install_dependencies.bat
    echo If you encounter module missing errors, run: install_dependencies.bat
    pause
) else (
    echo 应用正在运行。请在浏览器中访问 http://localhost:5001
    echo Application is running. Please visit http://localhost:5001 in your browser
    pause
) 