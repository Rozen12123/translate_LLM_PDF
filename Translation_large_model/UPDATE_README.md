# 审计报告翻译工具更新说明

## 项目清理与优化

我们对项目进行了全面清理和优化：

1. 删除了多余和过时的文件
   - 移除了基于Flask的旧版实现（web_app.py）
   - 删除了被替代的简化版翻译器和各种测试文件
   - 清理了未使用的GUI实现和相关支持文件

2. 保留核心组件
   - 简化版网页应用（simplified_web_app.py）
   - DeepSeek翻译器（deepseek_translator.py）
   - 表格处理模块（enhanced_table_handler.py）
   - 命令行工具（translate_cli.py）

## 依赖项更新

更新了依赖安装脚本（install_dependencies.bat/sh）：
- 确保正确安装tqdm依赖，修复之前的启动错误
- 将依赖分为基础组件和增强组件两类
- 即使部分增强依赖安装失败，基础功能仍可正常运行

## 文件命名更新

修改了翻译文件的命名规则，现在翻译后的文件将使用原文件名加上 `-英文版` 后缀，而不是之前的 `_translated` 后缀。

例如:
- 原文件: `财务报告2023.pdf`
- 翻译后: `财务报告2023-英文版.pdf`

## 服务端口更新

网页服务现在运行在端口5001（而不是之前的8000或5000），以避免端口冲突。

## 使用方法

### 网页界面

1. 运行安装脚本安装依赖
   - Windows: `install_dependencies.bat`
   - Linux/Mac: `./install_dependencies.sh`

2. 运行启动脚本
   - Windows: `run_simplified_web.bat`
   - Linux/Mac: `./run_simplified_web.sh`

3. 在浏览器中访问 http://localhost:5001
4. 上传PDF文件并选择翻译模型类型
5. 等待翻译完成后下载翻译好的文件

### 命令行工具

基本用法:
```
python translate_cli.py 你的文件.pdf
```

指定输出文件和模型:
```
python translate_cli.py 你的文件.pdf -o 输出文件.pdf -m professional
```

可用的模型类型:
- `standard`: 标准模型
- `professional`: 专业模型（默认，推荐用于审计报告）
- `enhanced`: 增强模型（最自然流畅的翻译）

## 已知问题

如果运行网页版出现端口被占用的错误，可以编辑 `simplified_web_app.py` 文件，修改 `port` 变量的值。

## 详细变更

有关所有更改的详细信息，请查看 `CHANGES_SUMMARY.md` 文件。

## 联系支持

如有任何问题，请联系系统管理员获取支持。 