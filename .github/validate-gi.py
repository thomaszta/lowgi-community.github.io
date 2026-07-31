#!/usr/bin/env python3
"""
验证 GI 值的合理性
- GI 值必须在 0-100 范围内
- 低GI: ≤55
- 中GI: 56-69
- 高GI: ≥70
"""

import os
import sys
import re
import yaml
from pathlib import Path


def extract_gi_value(gi_str):
    """从字符串中提取 GI 数值"""
    if not gi_str:
        return None
    
    # 尝试匹配数字 (可能有 ± 范围)
    match = re.search(r'(\d+)', str(gi_str))
    if match:
        return int(match.group(1))
    return None


def validate_gi_file(file_path):
    """验证单个文件的 GI 值"""
    errors = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"无法读取文件: {e}"], []
    
    # 提取 frontmatter
    if not content.startswith('---'):
        return [], []
    
    parts = content.split('---')
    if len(parts) < 3:
        return [], []
    
    frontmatter_text = parts[1]
    
    try:
        data = yaml.safe_load(frontmatter_text)
    except:
        return [], []
    
    if not isinstance(data, dict):
        return [], []
    
    content_type = data.get('type', '')
    
    # Food 和 Product 类型需要 GI 值
    if content_type in ['Food', 'Product']:
        gi_value = data.get('gi_value', '')
        
        if not gi_value:
            # 警告：建议提供 GI 值
            warnings.append(f"建议添加 gi_value 字段")
            return [], warnings
        
        # 提取数值
        gi_num = extract_gi_value(gi_value)
        
        if gi_num is None:
            errors.append(f"GI 值格式错误: {gi_value}")
            return errors, warnings
        
        # 检查范围
        if gi_num < 0 or gi_num > 100:
            errors.append(f"GI 值超出合理范围 (0-100): {gi_num}")
        
        # 分类警告
        if gi_num <= 55:
            category = "低GI"
        elif gi_num <= 69:
            category = "中GI"
        else:
            category = "高GI"
        
        # 警告：如果提交高GI食品给出说明
        if category == "高GI" and content_type == 'Food':
            warnings.append(f"⚠️ 这是一个高GI食材 ({gi_num})，确认这是正确的分类吗？")
    
    return errors, warnings


def main():
    content_dir = Path('content')
    all_errors = []
    all_warnings = []
    
    # 遍历所有 md 文件
    for md_file in content_dir.rglob('*.md'):
        errors, warnings = validate_gi_file(md_file)
        if errors:
            all_errors.append(f"\n❌ {md_file}:")
            all_errors.extend([f"   {e}" for e in errors])
        if warnings:
            all_warnings.append(f"\n⚠️ {md_file}:")
            all_warnings.extend([f"   {e}" for e in warnings])
    
    if all_errors:
        print("=" * 60)
        print("GI 值验证失败!")
        print("=" * 60)
        for e in all_errors:
            print(e)
        print("=" * 60)
        sys.exit(1)
    
    if all_warnings:
        print("=" * 60)
        print("GI 值警告 (请确认):")
        print("=" * 60)
        for w in all_warnings:
            print(w)
        print("=" * 60)
        # 警告不阻止提交，但会在 PR 中显示
    
    print("✅ GI 值验证通过!")
    sys.exit(0)


if __name__ == '__main__':
    main()
