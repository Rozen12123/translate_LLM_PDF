#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DeepSeek 审计报告翻译器命令行版
直接从命令行运行翻译功能，不需要web服务器
"""

import os
import sys
import argparse
from pathlib import Path
from deepseek_translator import DeepSeekTranslator

def main():
    parser = argparse.ArgumentParser(description='DeepSeek审计报告翻译器')
    parser.add_argument('input', help='输入PDF文件路径')
    parser.add_argument('-o', '--output', help='输出PDF文件路径（可选）')
    parser.add_argument('-m', '--model', choices=['standard', 'professional', 'enhanced'],
                      default='professional', help='翻译模型类型（标准, 专业, 增强）')
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    model_type = args.model
    
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在：{input_path}")
        return 1
    
    # 如果未指定输出路径，则自动生成
    if output_path is None:
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        output_path = os.path.join(os.path.dirname(input_path), f"{name}-英文版{ext}")
    
    print(f"使用{model_type}模型翻译 {input_path} 到 {output_path}")
    
    try:
        # 创建翻译器并翻译
        translator = DeepSeekTranslator(model_type=model_type)
        result = translator.translate_file(input_path, output_path)
        
        if result:
            print(f"翻译成功! 输出文件: {output_path}")
            return 0
        else:
            print(f"翻译失败，请查看日志获取详细信息。")
            return 1
    except Exception as e:
        print(f"翻译过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    # 如果没有命令行参数，显示使用方法
    if len(sys.argv) == 1:
        print("DeepSeek审计报告翻译器命令行版")
        print("\n用法示例:")
        print("  python translate_cli.py input.pdf -o output.pdf -m professional")
        print("\n可用的模型类型:")
        print("  standard     - 标准模型")
        print("  professional - 专业模型（默认，推荐用于审计报告）")
        print("  enhanced     - 增强模型（最自然流畅的翻译）")
        print("\n请确保您已经安装了所有必要的依赖项:")
        print("  pip install PyPDF2 reportlab requests tqdm")
        sys.exit(0)
    
    sys.exit(main()) 