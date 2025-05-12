# 审计报告翻译工具

这是一个专为中文审计报告翻译成英文而设计的工具，能够保持原始格式并提供高质量的审计专业术语翻译。

## 功能特点

- 支持从中文到英文的审计报告翻译
- 保留PDF原始格式和布局
- 提供专业审计术语的准确翻译
- 支持表格结构的保留和翻译
- 输出文件名采用"原文件名-英文版.pdf"格式
- 提供网页界面和命令行两种使用方式
- 支持三种翻译模式：标准、专业、增强

## 安装方法

### Windows系统

1. 确保安装了Python 3.8或更高版本
2. 下载或克隆本项目
3. 运行`install_dependencies.bat`安装所需依赖

### Linux/Mac系统

1. 确保安装了Python 3.8或更高版本
2. 下载或克隆本项目
3. 给脚本添加执行权限：`chmod +x *.sh`
4. 运行`./install_dependencies.sh`安装所需依赖

## 使用方法

### 网页界面（推荐）

1. Windows系统运行`run_simplified_web.bat`
   Linux/Mac系统运行`./run_simplified_web.sh`
2. 在浏览器中访问：http://localhost:5001
3. 上传要翻译的PDF文件并选择翻译模式
4. 等待翻译完成后下载翻译好的文件

### 命令行使用

基本用法:
```
python translate_cli.py 你的文件.pdf
```

指定输出文件和翻译模式:
```
python translate_cli.py 你的文件.pdf -o 输出文件.pdf -m professional
```

## 翻译模式说明

1. **标准模式 (standard)** - 基础翻译模式，专注于准确性
2. **专业模式 (professional)** - 推荐模式，着重审计专业术语的精确翻译
3. **增强模式 (enhanced)** - 提供更自然流畅的翻译，但可能花费更多时间

## 项目结构

```
├── simplified_web_app.py   # 网页应用主程序
├── deepseek_translator.py  # DeepSeek翻译器实现
├── enhanced_table_handler.py # 表格处理模块
├── translate_cli.py        # 命令行工具
├── run_simplified_web.bat  # Windows运行脚本
├── run_simplified_web.sh   # Linux/Mac运行脚本
├── install_dependencies.bat # Windows安装依赖脚本
├── install_dependencies.sh # Linux/Mac安装依赖脚本
├── requirements.txt        # 依赖清单
├── audit_terms.json        # 审计术语库
├── enhanced_audit_terms.json # 增强版审计术语库
├── uploads/                # 上传文件存储目录
├── results/                # 翻译结果存储目录
└── static/                 # 静态资源目录
```

## 常见问题

1. **缺少依赖项**
   如果遇到"ModuleNotFoundError"错误，请运行相应系统的依赖安装脚本。

2. **端口已被占用**
   如果遇到端口5001被占用的错误，可以修改`simplified_web_app.py`文件中的端口号。

3. **翻译速度慢**
   专业和增强模式的翻译会更加精确，但耗时也更长，请耐心等待。

## 更新说明

最新更新：
- 重构了文件命名规则，采用"原文件名-英文版.pdf"格式
- 更新了依赖安装脚本，修复了tqdm依赖问题
- 优化了项目结构，移除了多余文件
- 更新了错误处理机制

详细变更请查看`CHANGES_SUMMARY.md`文件。 