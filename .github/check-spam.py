#!/usr/bin/env python3
"""
检查内容质量
- sources 字段是否填写
- 是否包含黑名单食品（不是低GI的）
"""

import os
import sys
import re
import yaml
from pathlib import Path

# 低GI食品黑名单（明显不是低GI的食物）
BLACKLIST_FOODS = [
    '薯片', '薯条', '炸鸡', '可乐', '雪碧',
    '糖果', '巧克力', '蛋糕', '饼干', '雪糕',
    '方便面', '油条', '麻花', '月饼'
]


def check_file(file_path):
    """检查单个文件"""
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
    
    # 检查来源字段是否存在且非空（OKF v0.2 sources，兼容旧 source）
    has_source = bool(data.get('sources')) or bool(str(data.get('source', '')).strip())
    if not has_source:
        # Food 和 Product 必须有来源
        content_type = data.get('type', '')
        if content_type in ['Food', 'Product']:
            # 警告而非错误，因为 CI 会区分 warning 和 error
            warnings.append(f"⚠️ 建议添加 sources 字段，注明数据来源")
    
    # 检查标题是否在黑名单中
    title = data.get('title', '')
    for food in BLACKLIST_FOODS:
        if food in title:
            warnings.append(f"⚠️ 标题 '{title}' 包含 '{food}'，请确认这是低GI食品")
    
    return errors, warnings


def main():
    content_dir = Path('content')
    all_errors = []
    all_warnings = []
    
    for md_file in content_dir.rglob('*.md'):
        errors, warnings = check_file(md_file)
        if errors:
            all_errors.append(f"\n❌ {md_file}:")
            all_errors.extend([f"   {e}" for e in errors])
        if warnings:
            all_warnings.append(f"\n⚠️ {md_file}:")
            all_warnings.extend([f"   {e}" for e in warnings])
    
    if all_errors:
        print("=" * 60)
        print("内容审核失败!")
        print("=" * 60)
        for e in all_errors:
            print(e)
        print("=" * 60)
        print("\n请修复以上问题后重新提交。")
        sys.exit(1)
    
    if all_warnings:
        print("=" * 60)
        print("内容建议 (请确认):")
        print("=" * 60)
        for w in all_warnings:
            print(w)
        print("=" * 60)
        # 警告不阻止提交
    
    print("✅ 内容审核通过!")
    sys.exit(0)


if __name__ == '__main__':
    main()
