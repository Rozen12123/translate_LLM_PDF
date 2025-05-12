#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强型表格处理模块
用于检测、提取和重建PDF中的表格，保持原始格式
"""

import re
import logging
import numpy as np
from collections import defaultdict

# 尝试导入tqdm进度条，但不要在其不可用时失败
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # 创建一个简单的无操作tqdm替代品
    class tqdm:
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable
            
        def __iter__(self):
            return iter(self.iterable)
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args, **kwargs):
            pass
            
        def update(self, n=1):
            pass
            
        def close(self):
            pass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TableDetector:
    """检测文本中的表格结构"""
    
    @staticmethod
    def is_likely_table_row(line):
        """
        判断一行文本是否可能是表格行
        
        Args:
            line: 文本行
            
        Returns:
            bool: 是否可能是表格行
        """
        # 表格行通常有以下特征之一：
        # 1. 包含多个制表符或多个连续空格
        # 2. 包含多个数字且以制表符或多个空格分隔
        # 3. 包含表格分隔符 "|" 或 "+"
        
        # 检查表格分隔符
        if "|" in line or "+" in line:
            return True
        
        # 检查是否包含多个制表符（或4个以上连续空格的模式）
        if "\t" in line or re.search(r'\s{4,}', line):
            return True
        
        # 检查是否包含多个数字且以空格分隔
        numbers = re.findall(r'\d+(?:\.\d+)?', line)
        if len(numbers) >= 3 and re.search(r'\d+\s+\d+', line):
            return True
            
        return False
    
    @staticmethod
    def detect_table_in_text(text):
        """
        检测文本中的表格结构并标记
        
        Args:
            text: 输入文本
            
        Returns:
            标记后的文本和是否包含表格的布尔值
        """
        lines = text.split('\n')
        marked_lines = []
        has_table = False
        in_table = False
        table_start_index = -1
        
        for i, line in enumerate(lines):
            if TableDetector.is_likely_table_row(line):
                if not in_table:
                    in_table = True
                    has_table = True
                    table_start_index = i
                    marked_lines.append("<TABLE_START>")
                
                # 标记表格行
                marked_lines.append(f"<TABLE_ROW>{line}")
            else:
                if in_table:
                    in_table = False
                    marked_lines.append("<TABLE_END>")
                
                marked_lines.append(line)
        
        # 如果文本末尾是表格的一部分，添加结束标记
        if in_table:
            marked_lines.append("<TABLE_END>")
        
        return '\n'.join(marked_lines), has_table

class TableProcessor:
    """处理和重建表格"""
    
    @staticmethod
    def extract_tables(text):
        """
        从文本中提取表格结构
        
        Args:
            text: 输入文本
            
        Returns:
            表格列表和非表格内容
        """
        tables = []
        non_table_parts = []
        
        # 使用正则表达式查找所有表格
        table_pattern = r'<TABLE_START>(.+?)<TABLE_END>'
        table_matches = re.finditer(table_pattern, text, re.DOTALL)
        
        last_end = 0
        for match in table_matches:
            # 添加表格前的非表格内容
            non_table_part = text[last_end:match.start()]
            if non_table_part.strip():
                non_table_parts.append(non_table_part)
            
            # 提取表格内容
            table_content = match.group(1).strip()
            table_rows = [line.replace("<TABLE_ROW>", "").strip() 
                         for line in table_content.split('\n') 
                         if line.strip() and "<TABLE_ROW>" in line]
            
            if table_rows:
                tables.append(table_rows)
            
            last_end = match.end()
        
        # 添加最后一个表格后的非表格内容
        if last_end < len(text):
            non_table_part = text[last_end:]
            if non_table_part.strip():
                non_table_parts.append(non_table_part)
        
        return tables, non_table_parts
    
    @staticmethod
    def translate_table(table_rows, translator_func):
        """
        翻译表格，保持原始结构
        
        Args:
            table_rows: 表格行列表
            translator_func: 翻译函数
            
        Returns:
            翻译后的表格行列表
        """
        translated_rows = []
        
        for row in table_rows:
            # 分析行结构
            if "|" in row:
                # 表格使用|分隔符
                cells = row.split("|")
                translated_cells = []
                
                for cell in cells:
                    if cell.strip():
                        # 只翻译非空单元格
                        translated_cell = translator_func(cell.strip())
                        # 保持原始对齐和间距
                        if cell.startswith(" "):
                            translated_cell = " " + translated_cell
                        if cell.endswith(" "):
                            translated_cell = translated_cell + " "
                        translated_cells.append(translated_cell)
                    else:
                        translated_cells.append(cell)
                
                translated_row = "|".join(translated_cells)
            else:
                # 表格可能使用空格或制表符作为分隔符
                # 此情况下，先尝试将行按空格分割为单元格
                cells = re.split(r'\s{2,}|\t', row)
                if len(cells) > 1:
                    translated_cells = [translator_func(cell.strip()) if cell.strip() else cell for cell in cells]
                    # 尝试保持原始行的格式
                    translated_row = "  ".join(translated_cells)
                else:
                    # 如果无法识别表格结构，整行翻译
                    translated_row = translator_func(row)
            
            translated_rows.append(translated_row)
        
        return translated_rows
    
    @staticmethod
    def rebuild_text_with_tables(tables, non_table_parts, translator_func):
        """
        重建包含表格和非表格内容的文本
        
        Args:
            tables: 表格列表
            non_table_parts: 非表格内容列表
            translator_func: 翻译函数
            
        Returns:
            重建后的文本
        """
        result_parts = []
        
        # 交替添加非表格内容和表格
        for i in range(max(len(tables), len(non_table_parts))):
            # 添加非表格内容
            if i < len(non_table_parts):
                translated_text = translator_func(non_table_parts[i])
                result_parts.append(translated_text)
            
            # 添加表格
            if i < len(tables):
                translated_table = TableProcessor.translate_table(tables[i], translator_func)
                result_parts.append("\n".join(translated_table))
        
        return "\n\n".join(result_parts)

def process_text_with_tables(text, translator_func):
    """
    处理可能包含表格的文本
    
    Args:
        text: 输入文本
        translator_func: 翻译函数
        
    Returns:
        处理后的文本
    """
    # 检测并标记表格
    marked_text, has_table = TableDetector.detect_table_in_text(text)
    
    if has_table:
        logger.info("检测到表格结构，使用特殊表格处理")
        # 提取表格和非表格内容
        tables, non_table_parts = TableProcessor.extract_tables(marked_text)
        
        # 重建文本，保持表格结构
        return TableProcessor.rebuild_text_with_tables(tables, non_table_parts, translator_func)
    else:
        # 没有表格，直接翻译
        return translator_func(text)

# 测试代码
if __name__ == "__main__":
    # 示例表格文本
    sample_text = """
项目  | 本期金额 | 上期金额
------|---------|--------
收入  | 10,000  | 8,500
成本  | 6,500   | 5,200
利润  | 3,500   | 3,300

这是一段普通文本，不是表格的一部分。

资产负债表
资产项目  | 期末余额 | 期初余额
---------|---------|--------
流动资产  | 50,000  | 45,000
非流动资产| 120,000 | 110,000
资产总计  | 170,000 | 155,000
    """
    
    # 示例翻译函数
    def mock_translator(text):
        # 这只是一个示例，实际应使用真正的翻译功能
        translations = {
            "项目": "Item",
            "本期金额": "Current Period",
            "上期金额": "Previous Period",
            "收入": "Revenue",
            "成本": "Cost",
            "利润": "Profit",
            "这是一段普通文本，不是表格的一部分。": "This is a regular text, not part of a table.",
            "资产负债表": "Balance Sheet",
            "资产项目": "Asset Items",
            "期末余额": "Ending Balance",
            "期初余额": "Beginning Balance",
            "流动资产": "Current Assets",
            "非流动资产": "Non-current Assets",
            "资产总计": "Total Assets"
        }
        
        for zh, en in translations.items():
            if zh in text:
                text = text.replace(zh, en)
        
        return text
    
    # 处理带表格的文本
    result = process_text_with_tables(sample_text, mock_translator)
    print(result) 