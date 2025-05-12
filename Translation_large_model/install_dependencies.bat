@echo off
echo 安装审计报告翻译工具所需的依赖项...
echo Installing dependencies for Audit Report Translation Tool...

echo 正在安装基础依赖项...
echo Installing basic dependencies...
pip install PyPDF2==3.0.1 reportlab==4.0.4 requests tqdm==4.65.0

if errorlevel 1 (
    echo 安装依赖项时出错。请检查您的Python环境并手动安装依赖项。
    echo Error installing dependencies. Please check your Python environment and install dependencies manually.
    echo pip install PyPDF2==3.0.1 reportlab==4.0.4 requests tqdm==4.65.0
    pause
    exit /b 1
)

echo 安装表格处理依赖项...
echo Installing table handling dependencies...
pip install numpy==1.24.3 pandas==2.0.3

if errorlevel 1 (
    echo 警告：表格处理依赖项安装失败，但基础功能应该可以正常工作。
    echo Warning: Table handling dependencies failed to install, but basic functionality should work.
) 

echo 依赖项安装成功!
echo Dependencies installed successfully!
echo.
echo 现在您可以运行 run_simplified_web.bat 启动翻译工具。
echo You can now run run_simplified_web.bat to start the translation tool.
pause 