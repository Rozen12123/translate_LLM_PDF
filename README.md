# AuditTranslate 使用指南

本文档将帮助审计专业人员快速上手 AuditTranslate 工具，实现审计报告的高质量翻译。

## 目录

1. [基本用法](#基本用法)
2. [处理不同类型的审计报告](#处理不同类型的审计报告)
3. [批量处理多份报告](#批量处理多份报告)
4. [专业术语定制](#专业术语定制)
5. [常见问题解答](#常见问题解答)

## 基本用法

### 安装

```bash
pip install pdf2zh
```

### 翻译单份审计报告

```bash
pdf2zh 您的审计报告.pdf
```

执行上述命令后，程序将在当前工作目录生成两个文件：

- `您的审计报告-mono.pdf`: 纯中文翻译版本
- `您的审计报告-dual.pdf`: 中英双语对照版本

### 使用图形界面

如果您不熟悉命令行，可以使用图形界面：

```bash
pdf2zh -i
```

浏览器会自动打开 http://localhost:7860/ 页面，您可以通过拖放或选择文件进行翻译。

## 处理不同类型的审计报告

### 年度财务审计报告

```bash
pdf2zh 财务审计报告.pdf -s deepl
```

使用 DeepL 翻译引擎可以获得更好的财务术语翻译质量。

### 内部控制评估报告

```bash
pdf2zh 内控评估报告.pdf --prompt audit_terms.txt
```

使用自定义的审计术语对照表（已随软件附带）可以提高内控术语翻译准确性。

### 合规性审计报告

```bash
pdf2zh 合规审计.pdf -s google -lo zh
```

合规报告通常包含大量法规引用，使用Deepl翻译通常能获得较好效果。

## 批量处理多份报告

### 批量翻译整个文件夹的报告

```bash
pdf2zh --dir /path/to/reports/
```

### 设置输出目录

```bash
pdf2zh 审计报告.pdf -o /path/to/output/
```

## 专业术语定制

AuditTranslate 包含一个审计专业术语库，但您可能需要针对特定行业或客户定制术语：

### 修改术语库

您可以编辑 `audit_terms.txt` 文件，添加或修改特定术语：

```
# 格式：英文术语=中文术语
qualified opinion=保留意见
```

### 使用自定义术语库

```bash
pdf2zh 审计报告.pdf --prompt your_custom_terms.txt
```

### 针对特定行业的术语

对于特定行业的审计报告，我们建议创建行业特定的术语表：

- `banking_terms.txt`: 银行业审计术语
- `insurance_terms.txt`: 保险业审计术语
- `manufacturing_terms.txt`: 制造业审计术语

## 常见问题解答

### Q: 如何确保表格中的数据正确显示？

A: AuditTranslate 默认保留表格格式。如果发现表格错位，可以尝试使用兼容模式：

```bash
pdf2zh 审计报告.pdf -cp
```

### Q: 报告包含敏感财务数据，如何确保数据安全？

A: AuditTranslate 完全在本地运行，不会将您的文档上传到互联网。如果使用 OpenAI 等第三方翻译服务，请注意他们的隐私政策。

### Q: 如何翻译带有图章和签名的审计报告？

A: AuditTranslate 会保留原始图章和签名。对于扫描版pdf，使用以下命令可提高识别质量：

```bash
pdf2zh 扫描版审计报告.pdf -cp
```

### Q: 如何处理多语言审计报告（如境外子公司报告）？

A: 您可以指定源语言和目标语言：

```bash
pdf2zh 英文审计报告.pdf -li en -lo zh  # 英文翻译为中文
pdf2zh 日文审计报告.pdf -li ja -lo zh  # 日文翻译为中文
```

### Q: 翻译后的审计报告法律效力如何？

A: 翻译版本仅供参考，无法取代原始审计报告的法律效力。建议在文档中添加免责声明，说明这是机器翻译版本。

---

如有其他问题，请联系项目维护者：[R](mailto:your.email@example.com)ozen
