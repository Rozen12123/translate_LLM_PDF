#!/bin/bash

echo "正在启动审计报告翻译工具简易网页版..."
echo "Starting Simplified Audit Report Translator Web Application..."

# 检查是否安装了必要的依赖项
python3 -c "import PyPDF2, reportlab, requests, tqdm" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误: 缺少必要的依赖项。"
    echo "Error: Missing required dependencies."
    echo ""
    echo "请先运行 ./install_dependencies.sh 或手动安装依赖项:"
    echo "Please run ./install_dependencies.sh or manually install dependencies:"
    echo "pip install PyPDF2 reportlab requests tqdm"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

# 确保脚本可执行
chmod +x ./install_dependencies.sh

# 运行应用
python3 simplified_web_app.py
if [ $? -ne 0 ]; then
    echo "启动应用时出错。请查看上面的错误信息。"
    echo "Error starting application. Please check the error message above."
    echo ""
    echo "如果遇到模块缺失错误，请运行: ./install_dependencies.sh"
    echo "If you encounter module missing errors, run: ./install_dependencies.sh"
    read -p "Press Enter to continue..."
else
    echo "应用正在运行。请在浏览器中访问 http://localhost:5001"
    echo "Application is running. Please visit http://localhost:5001 in your browser"
    read -p "Press Enter to continue..."
fi 