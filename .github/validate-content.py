#!/usr/bin/env python3
"""
验证 Markdown 文件的 YAML frontmatter
- 检查必填字段
- 检查字段格式
"""

import os
import sys
import re
import yaml
from pathlib import Path

# 必填字段
REQUIRED_FIELDS = {
    'Food': ['type', 'title', 'description', 'tags', 'source', 'lang'],
    'Product': ['type', 'title', 'description', 'gi_value', 'tags', 'source', 'lang'],
    'Recipe': ['type', 'title', 'description', 'tags', 'source', 'lang'],
    'Concept': ['type', 'title', 'description', 'lang'],
    'Guide': ['type', 'title', 'description', 'lang'],
}

# 所有类型都需要 lang
ALL_REQUIRED = ['lang']

def validate_frontmatter(file_path):
    """验证单个文件的 frontmatter"""
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"无法读取文件: {e}"]
    
    # 检查 frontmatter 分隔符
    if not content.startswith('---'):
        return ["文件缺少 YAML frontmatter (需要以 --- 开头)"]
    
    # 提取 frontmatter
    parts = content.split('---')
    if len(parts) < 3:
        return ["YAML frontmatter 格式错误 (需要 --- 开头和结尾)"]
    
    frontmatter_text = parts[1]
    
    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        return [f"YAML 解析错误: {e}"]
    
    if not isinstance(data, dict):
        return ["YAML frontmatter 必须是键值对"]
    
    # 获取内容类型
    content_type = data.get('type', '')
    
    # 检查必填字段
    required = REQUIRED_FIELDS.get(content_type, [])
    for field in required:
        if field not in data or not data[field]:
            errors.append(f"缺少必填字段: {field}")
    
    # 检查 lang 字段
    if 'lang' not in data:
        errors.append("缺少 lang 字段 (zh 或 en)")
    elif data['lang'] not in ['zh', 'en']:
        errors.append(f"lang 字段必须是 'zh' 或 'en'，当前值: {data['lang']}")
    
    # 检查 tags 格式
    if 'tags' in data:
        if not isinstance(data['tags'], list):
            errors.append("tags 必须是数组格式: [标签1, 标签2]")
    
    return errors


def main():
    content_dir = Path('content')
    errors = []
    
    # 遍历所有 md 文件
    for md_file in content_dir.rglob('*.md'):
        file_errors = validate_frontmatter(md_file)
        if file_errors:
            errors.append(f"\n❌ {md_file}:")
            errors.extend([f"   {e}" for e in file_errors])
    
    if errors:
        print("=" * 60)
        print("内容验证失败!")
        print("=" * 60)
        for e in errors:
            print(e)
        print("=" * 60)
        print("\n请修复以上问题后重新提交。")
        print("参考: https://github.com/thomaszta/lowgi-community.github.io/blob/master/CONTRIBUTING.md")
        sys.exit(1)
    else:
        print("✅ 所有内容验证通过!")
        sys.exit(0)


if __name__ == '__main__':
    main()
