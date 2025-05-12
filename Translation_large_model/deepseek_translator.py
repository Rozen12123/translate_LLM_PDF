import os
import json
import re
import time
import logging
import tempfile
import requests
from pathlib import Path
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入tqdm进度条，但不要在其不可用时失败
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("未找到tqdm模块，将使用简单进度显示")
    # 创建一个简单的无操作tqdm替代品
    class tqdm:
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable
            self.total = len(iterable) if iterable is not None else 0
            self.n = 0
            self.desc = kwargs.get('desc', '')
            if self.total > 0:
                logger.info(f"{self.desc}: 开始处理 {self.total} 项")
            
        def __iter__(self):
            for item in self.iterable:
                yield item
                self.n += 1
                if self.n % 5 == 0 or self.n == self.total:  # 每5项或最后一项记录一次进度
                    logger.info(f"{self.desc}: {self.n}/{self.total} 完成")
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args, **kwargs):
            if self.total > 0:
                logger.info(f"{self.desc}: 所有 {self.total} 项处理完成")
            
        def update(self, n=1):
            self.n += n
            
        def close(self):
            pass

# 导入增强型表格处理模块
try:
    from enhanced_table_handler import process_text_with_tables, TableDetector
    TABLE_HANDLER_AVAILABLE = True
    logger.info("成功导入增强型表格处理模块")
except ImportError:
    TABLE_HANDLER_AVAILABLE = False
    logger.warning("未找到增强型表格处理模块，将使用基本表格处理")

# DeepSeek API 配置
API_KEY = "sk-f6a6400b26704152b6a0e013d34ca6f1"  # 您的API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"

# 术语库 - 常见审计术语
AUDIT_TERMINOLOGY = {
    "审计报告": "Audit Report",
    "财务报表": "Financial Statements",
    "资产负债表": "Balance Sheet",
    "利润表": "Income Statement",
    "现金流量表": "Cash Flow Statement",
    "审计意见": "Audit Opinion",
    "无保留意见": "Unqualified Opinion",
    "保留意见": "Qualified Opinion",
    "否定意见": "Adverse Opinion",
    "无法表示意见": "Disclaimer of Opinion",
    "管理层责任": "Management's Responsibility",
    "注册会计师的责任": "Auditor's Responsibility",
    "重大错报风险": "Risk of Material Misstatement",
    "关键审计事项": "Key Audit Matters",
    "持续经营": "Going Concern",
    "内部控制": "Internal Control",
    "会计政策": "Accounting Policies",
    "会计估计": "Accounting Estimates",
    "重要性水平": "Materiality Level",
    "合并财务报表": "Consolidated Financial Statements",
    "财务状况": "Financial Position",
    "经营成果": "Operating Results"
}

class DeepSeekTranslator:
    """使用DeepSeek API的审计报告翻译器"""
    
    def __init__(self, api_key=API_KEY, model_type="professional"):
        """
        初始化翻译器
        
        Args:
            api_key: DeepSeek API密钥
            model_type: 翻译模型类型 (standard, professional, enhanced)
        """
        self.api_key = api_key
        self.model_type = model_type
        self.model_name = "deepseek-chat"  # DeepSeek默认模型
        
        # 根据模型类型设置模型参数
        if model_type == "professional":
            # 专业模型 - 更专注于审计术语的准确性
            self.temperature = 0.3
            self.max_tokens = 2000
            self.system_prompt = (
                "You are a professional financial translator specializing in audit reports. "
                "Translate the Chinese text to English with these requirements:\n"
                "1. Maintain professional audit and accounting terminology\n"
                "2. Ensure natural, fluent English with no machine-translation traces\n"
                "3. Preserve paragraph structure and formatting\n"
                "4. Preserve table structures and alignments if present\n"
                "5. Use formal business language appropriate for audit reports\n"
                "6. Be consistent with terminology throughout the document\n"
                "7. If you encounter tables, maintain the same structure and alignment\n"
                "8. For financial data in tables, keep the numbers exactly the same\n"
                "9. For headers and titles in tables, translate accurately but keep short and professional\n"
                "10. Ensure that sentences flow naturally in English, avoid overly literal translations"
            )
        elif model_type == "enhanced":
            # 增强模型 - 更自然流畅的翻译
            self.temperature = 0.4
            self.max_tokens = 2500
            self.system_prompt = (
                "You are an expert translator with deep knowledge of financial auditing. "
                "Translate the Chinese audit report text to English with these requirements:\n"
                "1. Create perfect, natural English that sounds like it was originally written in English\n"
                "2. Maintain all professional financial and audit terminology with precision\n"
                "3. Preserve the formal tone and structure of the original document\n" 
                "4. Ensure consistency in terminology throughout the translation\n"
                "5. Adapt Chinese expressions to their natural English counterparts rather than translating literally\n"
                "6. Preserve any table structures, maintaining the same layout and alignment\n"
                "7. Keep all numbers and data values exactly the same when translating tables\n"
                "8. Pay special attention to proper formatting of dates, currency amounts, and percentages\n"
                "9. For technical terms specific to Chinese accounting standards, provide the closest international equivalent"
            )
        else:  # standard
            # 标准模型
            self.temperature = 0.1
            self.max_tokens = 1500
            self.system_prompt = (
                "You are a translator for audit reports. "
                "Translate the Chinese text to English accurately. "
                "Maintain proper audit terminology and document structure. "
                "Preserve table layouts and formats. "
                "Keep all numerical values the same."
            )
        
        logger.info(f"初始化DeepSeek翻译器，使用{model_type}模型")
        
    def call_deepseek_api(self, text_to_translate):
        """
        调用DeepSeek API进行翻译
        
        Args:
            text_to_translate: 要翻译的中文文本
            
        Returns:
            翻译后的英文文本
        """
        client = OpenAI(api_key=self.api_key, base_url=API_URL)
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Translate this Chinese audit report text to English:\n\n{text_to_translate}"}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False
        )
        
        translated_text = response.choices[0].message.content
        return translated_text
    
    def pre_process_text(self, text):
        """
        预处理文本以提高翻译质量
        
        Args:
            text: 原始中文文本
            
        Returns:
            预处理后的文本
        """
        # 检测是否包含表格结构
        table_pattern = r'[|\+][-+]+[|\+]'
        has_table = bool(re.search(table_pattern, text))
        
        # 如果检测到表格，添加特殊标记以保留结构
        if has_table:
            # 标记表格开始
            text = re.sub(r'([|\+][-+]+[|\+])', r'<TABLE_START>\n\1', text)
            # 保留表格行
            text = re.sub(r'(\|[^|]+\|)', r'<TABLE_ROW>\1', text)
            # 标记表格结束
            text = re.sub(r'([|\+][-+]+[|\+])\s*(?!\n[|\+])', r'\1\n<TABLE_END>', text)
        
        # 替换关键专业术语
        for zh_term, en_term in AUDIT_TERMINOLOGY.items():
            # 使用命名分组来保留匹配的术语，同时添加标记
            text = re.sub(f'({re.escape(zh_term)})', f'<TERM>{zh_term}</TERM>', text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def post_process_translation(self, translation):
        """
        后处理以提高翻译质量
        
        Args:
            translation: 原始翻译文本
            
        Returns:
            处理后的翻译文本
        """
        # 确保首字母大写
        if translation and len(translation) > 0:
            translation = translation[0].upper() + translation[1:]
        
        # 确保句号后面的单词首字母大写
        translation = re.sub(r'\.(\s+)([a-z])', lambda m: f'.{m.group(1)}{m.group(2).upper()}', translation)
        
        # 修复常见的格式问题
        translation = translation.replace(" ,", ",")
        translation = translation.replace(" .", ".")
        translation = translation.replace(" :", ":")
        
        # 确保括号格式正确
        translation = re.sub(r'\(\s+', '(', translation)
        translation = re.sub(r'\s+\)', ')', translation)
        
        # 恢复表格标记
        translation = translation.replace("<TABLE_START>", "")
        translation = translation.replace("<TABLE_END>", "")
        translation = translation.replace("<TABLE_ROW>", "")
        
        # 保留数字格式
        # 查找金额模式并确保没有不必要的空格
        translation = re.sub(r'(\d+)\s+,\s+(\d+)', r'\1,\2', translation)
        translation = re.sub(r'(\d+)\s+\.\s+(\d+)', r'\1.\2', translation)
        
        # 确保百分比格式正确
        translation = re.sub(r'(\d+)\s+%', r'\1%', translation)
        
        return translation
        
    def translate_text(self, text, chunk_size=1500):
        """
        翻译文本，处理长文本
        
        Args:
            text: 要翻译的中文文本
            chunk_size: 每个分块的最大字符数
            
        Returns:
            翻译后的英文文本
        """
        if not text or text.strip() == "":
            return ""
        
        # 预处理文本
        processed_text = self.pre_process_text(text)
        
        # 检查是否包含表格
        has_table = False
        if hasattr(processed_text, 'count') and ("<TABLE_START>" in processed_text or "|" in processed_text):
            has_table = True
            logger.info("检测到可能包含表格的文本")
        
        # 对于短文本，直接翻译
        if len(processed_text) < chunk_size:
            try:
                # 如果文本包含表格且表格处理模块可用，使用特殊处理
                if has_table and TABLE_HANDLER_AVAILABLE:
                    logger.info("使用增强型表格处理模块翻译包含表格的文本")
                    
                    # 创建一个封装的翻译函数，提供给表格处理器使用
                    def translate_func(text_to_translate):
                        if not text_to_translate or text_to_translate.strip() == "":
                            return ""
                        return self.call_deepseek_api(text_to_translate)
                    
                    translation = process_text_with_tables(processed_text, translate_func)
                else:
                    translation = self.call_deepseek_api(processed_text)
                    
                return self.post_process_translation(translation)
            except Exception as e:
                logger.error(f"翻译短文本时出错: {str(e)}")
                # 如果翻译失败，返回带有错误提示的原文
                return f"[Translation Error: {str(e)}]"
        
        # 对于长文本，按段落拆分并分别翻译
        paragraphs = processed_text.split('\n')
        translated_paragraphs = []
        
        current_chunk = []
        current_length = 0
        
        for para in tqdm(paragraphs, desc="翻译段落"):
            # 如果段落很长，需要再次分割
            if len(para) > chunk_size:
                # 检查段落是否包含表格结构
                if has_table and ("<TABLE_ROW>" in para or "|" in para) and TABLE_HANDLER_AVAILABLE:
                    logger.info("翻译包含表格的长段落")
                    
                    def translate_func(text_to_translate):
                        if not text_to_translate or text_to_translate.strip() == "":
                            return ""
                        return self.call_deepseek_api(text_to_translate)
                    
                    translated_paragraph = process_text_with_tables(para, translate_func)
                    translated_paragraphs.append(self.post_process_translation(translated_paragraph))
                    continue
                
                # 按句子分割长段落
                sentences = re.split(r'(。|！|？|\.|\!|\?)', para)
                sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2] + [""])]
                
                current_sentence_chunk = []
                current_sentence_length = 0
                
                for sentence in sentences:
                    if current_sentence_length + len(sentence) > chunk_size and current_sentence_chunk:
                        # 翻译当前句子块
                        sentence_text = "".join(current_sentence_chunk)
                        try:
                            translated_sentence = self.call_deepseek_api(sentence_text)
                            translated_paragraphs.append(self.post_process_translation(translated_sentence))
                        except Exception as e:
                            logger.error(f"翻译句子块时出错: {str(e)}")
                            translated_paragraphs.append(f"[Translation Error: {str(e)}]")
                        
                        # 重置句子块
                        current_sentence_chunk = [sentence]
                        current_sentence_length = len(sentence)
                    else:
                        current_sentence_chunk.append(sentence)
                        current_sentence_length += len(sentence)
                
                # 处理剩余的句子
                if current_sentence_chunk:
                    sentence_text = "".join(current_sentence_chunk)
                    try:
                        translated_sentence = self.call_deepseek_api(sentence_text)
                        translated_paragraphs.append(self.post_process_translation(translated_sentence))
                    except Exception as e:
                        logger.error(f"翻译最后句子块时出错: {str(e)}")
                        translated_paragraphs.append(f"[Translation Error: {str(e)}]")
            
            # 处理正常长度的段落
            elif current_length + len(para) > chunk_size and current_chunk:
                # 翻译当前段落块
                chunk_text = "\n".join(current_chunk)
                try:
                    # 检查块是否包含表格
                    if has_table and ("<TABLE_ROW>" in chunk_text or "|" in chunk_text) and TABLE_HANDLER_AVAILABLE:
                        logger.info("翻译包含表格的段落块")
                        
                        def translate_func(text_to_translate):
                            if not text_to_translate or text_to_translate.strip() == "":
                                return ""
                            return self.call_deepseek_api(text_to_translate)
                        
                        translated_chunk = process_text_with_tables(chunk_text, translate_func)
                    else:
                        translated_chunk = self.call_deepseek_api(chunk_text)
                    
                    translated_paragraphs.append(self.post_process_translation(translated_chunk))
                except Exception as e:
                    logger.error(f"翻译段落块时出错: {str(e)}")
                    translated_paragraphs.append(f"[Translation Error: {str(e)}]")
                
                # 重置段落块
                current_chunk = [para]
                current_length = len(para)
            else:
                current_chunk.append(para)
                current_length += len(para)
        
        # 处理剩余的段落
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            try:
                # 检查剩余块是否包含表格
                if has_table and ("<TABLE_ROW>" in chunk_text or "|" in chunk_text) and TABLE_HANDLER_AVAILABLE:
                    logger.info("翻译最后包含表格的段落块")
                    
                    def translate_func(text_to_translate):
                        if not text_to_translate or text_to_translate.strip() == "":
                            return ""
                        return self.call_deepseek_api(text_to_translate)
                    
                    translated_chunk = process_text_with_tables(chunk_text, translate_func)
                else:
                    translated_chunk = self.call_deepseek_api(chunk_text)
                
                translated_paragraphs.append(self.post_process_translation(translated_chunk))
            except Exception as e:
                logger.error(f"翻译最后段落块时出错: {str(e)}")
                translated_paragraphs.append(f"[Translation Error: {str(e)}]")
        
        # 组合所有翻译后的文本
        return "\n".join(translated_paragraphs)
    
    def translate_pdf(self, input_path, output_path):
        """
        翻译PDF文件，保持原格式
        
        Args:
            input_path (str): 输入PDF文件路径
            output_path (str): 输出PDF文件路径
            
        Returns:
            bool: 翻译是否成功
        """
        try:
            logger.info(f"开始翻译PDF: {input_path}")
            
            # 先创建输出目录（如果不存在）
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 打开PDF文件
            with open(input_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                logger.info(f"PDF共有{num_pages}页")
                
                # 创建一个新的PDF
                output_pdf = PyPDF2.PdfWriter()
                
                # 处理每一页
                for page_num in range(num_pages):
                    logger.info(f"处理第{page_num+1}页...")
                    page = reader.pages[page_num]
                    
                    # 提取文本，同时保留页面中的所有非文本元素（如图像、形状等）
                    original_page = page
                    text = page.extract_text()
                    
                    # 将文本分成段落，保留原始布局结构
                    paragraphs = []
                    current_paragraph = []
                    lines = text.split('\n')
                    
                    for line in lines:
                        if not line.strip():  # 空行表示段落分隔
                            if current_paragraph:
                                paragraphs.append('\n'.join(current_paragraph))
                                current_paragraph = []
                        else:
                            current_paragraph.append(line)
                    
                    if current_paragraph:  # 添加最后一个段落
                        paragraphs.append('\n'.join(current_paragraph))
                    
                    # 翻译每个段落
                    logger.info(f"翻译第{page_num+1}页的文本...")
                    translated_paragraphs = []
                    for para in tqdm(paragraphs, desc="翻译段落"):
                        if para.strip():
                            translated_para = self.translate_text(para)
                            translated_paragraphs.append(translated_para)
                        else:
                            translated_paragraphs.append("")
                    
                    translated_text = '\n\n'.join(translated_paragraphs)
                    
                    # 创建临时PDF并写入翻译后的文本
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    # 获取原始页面大小和布局
                    mediabox = original_page.mediabox
                    width = float(mediabox.width)
                    height = float(mediabox.height)
                    
                    # 创建一个新的Canvas，匹配原始页面大小
                    c = canvas.Canvas(temp_path, pagesize=(width, height))
                    
                    # 设置更小的字体以确保内容能完整显示
                    c.setFont("Helvetica", 8)
                    
                    # 计算文本框位置和大小，增加可用区域
                    margin = 36  # 减小页边距（点）
                    text_width = width - 2 * margin
                    y_position = height - margin  # 开始位置
                    
                    # 分行写入，保持段落结构
                    for paragraph in translated_paragraphs:
                        if not paragraph.strip():
                            y_position -= 12  # 段落间空行
                            continue
                        
                        # 分割段落为行
                        lines = paragraph.split('\n')
                        for line in lines:
                            if not line.strip():
                                y_position -= 10
                                continue
                            
                            # 处理文本行 - 增强的文本处理
                            words = line.split(' ')
                            current_line = []
                            current_width = 0
                            
                            for word in words:
                                word_width = c.stringWidth(word + ' ', "Helvetica", 8)
                                
                                if current_width + word_width > text_width:
                                    # 当前行已满，写入并开始新行
                                    if current_line:
                                        if y_position < margin:  # 检查是否需要新页面
                                            c.showPage()
                                            c.setFont("Helvetica", 8)
                                            y_position = height - margin
                                        c.drawString(margin, y_position, ' '.join(current_line))
                                        y_position -= 10  # 行间距
                                        current_line = [word]
                                        current_width = word_width
                                    else:
                                        # 单词太长，需要断行
                                        if y_position < margin:
                                            c.showPage()
                                            c.setFont("Helvetica", 8)
                                            y_position = height - margin
                                        c.drawString(margin, y_position, word)
                                        y_position -= 10
                                        current_line = []
                                        current_width = 0
                                else:
                                    current_line.append(word)
                                    current_width += word_width
                            
                            # 写入最后一行
                            if current_line:
                                if y_position < margin:
                                    c.showPage()
                                    c.setFont("Helvetica", 8)
                                    y_position = height - margin
                                c.drawString(margin, y_position, ' '.join(current_line))
                                y_position -= 10
                        
                        # 段落后添加额外空间
                        y_position -= 6
                    
                    c.save()
                    
                    # 读取临时PDF并添加到输出文件
                    with open(temp_path, 'rb') as f:
                        temp_reader = PyPDF2.PdfReader(f)
                        for p in range(len(temp_reader.pages)):
                            output_pdf.add_page(temp_reader.pages[p])
                    
                    # 删除临时文件
                    os.unlink(temp_path)
                
                # 保存翻译后的PDF
                with open(output_path, 'wb') as output_file:
                    output_pdf.write(output_file)
                
                logger.info(f"翻译完成，已保存到: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"翻译过程出错: {str(e)}")
            return False
    
    def translate_file(self, input_path, output_path=None):
        """
        翻译文件的通用入口
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如未指定则自动生成
            
        Returns:
            str: 输出文件路径或None（如果失败）
        """
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            logger.error(f"输入文件不存在: {input_path}")
            return None
        
        # 如果未指定输出路径，则自动生成
        if output_path is None:
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(os.path.dirname(input_path), f"{name}-英文版{ext}")
        
        # 检查文件类型并翻译
        _, ext = os.path.splitext(input_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            success = self.translate_pdf(input_path, output_path)
            return output_path if success else None
        else:
            logger.error(f"不支持的文件类型: {ext}")
            return None

# 命令行入口
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='使用DeepSeek API翻译审计报告')
    parser.add_argument('input', help='输入PDF文件路径')
    parser.add_argument('-o', '--output', help='输出PDF文件路径（可选）')
    parser.add_argument('-m', '--model', choices=['standard', 'professional', 'enhanced'],
                        default='professional', help='翻译模型类型（标准, 专业, 增强）')
    
    args = parser.parse_args()
    
    # 创建翻译器并翻译
    translator = DeepSeekTranslator(model_type=args.model)
    output_path = translator.translate_file(args.input, args.output)
    
    if output_path:
        print(f"翻译成功! 输出文件: {output_path}")
    else:
        print(f"翻译失败，请查看日志获取详细信息。")
        sys.exit(1) 