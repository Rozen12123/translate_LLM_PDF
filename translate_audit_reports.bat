@echo off
REM AuditTranslate 一键式审计报告翻译工具
REM 作者：Your Name

echo ====================================================
echo         AuditTranslate 审计报告翻译工具
echo ====================================================
echo.

REM 检查环境变量
set HF_ENDPOINT=https://hf-mirror.com

REM 创建输出目录
if not exist "output" mkdir output

echo 请选择要执行的操作:
echo 1. 翻译单份审计报告
echo 2. 批量翻译reports文件夹中的所有报告
echo 3. 启动图形用户界面
echo 4. 退出
echo.

set /p choice=请输入选项(1-4): 

if "%choice%"=="1" (
    echo.
    set /p filename=请输入审计报告文件名(包括扩展名): 
    echo.
    echo 正在翻译 %filename%...
    echo 使用审计专业术语表进行翻译...
    pdf2zh "%filename%" -o output --prompt audit_terms.txt
    echo.
    echo 翻译完成! 文件保存在 output 文件夹中。
)

if "%choice%"=="2" (
    echo.
    echo 正在批量翻译报告...
    if not exist "reports" (
        echo 错误: reports文件夹不存在!
        echo 请创建reports文件夹并将待翻译的PDF文件放入其中。
        goto end
    )
    pdf2zh --dir reports -o output --prompt audit_terms.txt
    echo.
    echo 批量翻译完成! 所有文件已保存到 output 文件夹。
)

if "%choice%"=="3" (
    echo.
    echo 正在启动图形界面...
    start http://localhost:7860
    pdf2zh -i
)

if "%choice%"=="4" (
    goto end
)

:end
echo.
echo 感谢使用 AuditTranslate 审计报告翻译工具!
pause 