#!/usr/bin/env python3
"""
OKF → Static Site Generator
Reads OKF (Open Knowledge Format) markdown files and generates a clean static HTML site.
"""

import os
import re
import sys
import shutil
import json
from datetime import datetime, date
from pathlib import Path
from html import escape

import yaml
import markdown

SITE_URL = os.environ.get("SITE_URL", "https://thomaszta.github.io/lowgi-community.github.io").rstrip("/")
USE_RELATIVE = os.environ.get("LOCAL_DEV", "") == "1"
# 决定资源路径：本地开发用根相对路径，生产用绝对URL
# 使用 / 开头确保在任何页面深度下都能正确解析
ASSET_BASE = "/" if USE_RELATIVE else SITE_URL
CONTENT_DIR = "content"
OUTPUT_DIR = "site"
DEFAULT_LANG = "zh"

def dir_label(key, lang):
    LABELS = {
        "concepts": { "zh": "核心概念", "en": "Concepts" },
        "foods": { "zh": "食材库", "en": "Foods" },
        "recipes": { "zh": "食谱库", "en": "Recipes" },
        "guides": { "zh": "实用指南", "en": "Guides" },
        "community": { "zh": "社区", "en": "Community" },
        "products": { "zh": "成品食品", "en": "Products" },
        "grains": { "zh": "谷类", "en": "Grains" },
        "legumes": { "zh": "豆类", "en": "Legumes" },
        "vegetables": { "zh": "蔬菜", "en": "Vegetables" },
        "fruits": { "zh": "水果", "en": "Fruits" },
        "proteins": { "zh": "蛋白质", "en": "Proteins" },
        "breads": { "zh": "面包类", "en": "Breads" },
        "noodles": { "zh": "面条类", "en": "Noodles" },
        "snacks": { "zh": "零食类", "en": "Snacks" },
        "beverages": { "zh": "饮品类", "en": "Beverages" },
        "condiments": { "zh": "调味品类", "en": "Condiments" },
        "breakfast": { "zh": "早餐", "en": "Breakfast" },
        "main-meals": { "zh": "正餐", "en": "Main Meals" },
    }
    if key in LABELS:
        return LABELS[key].get(lang, key)
    if lang == "zh":
        return key
    return key.replace("-", " ").title()

# SVG Icons (Heroicons) - 简洁矢量图标
SVG_ICONS = {
    # 顶级分类图标
    "foods": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 21h10M12 3v18M5.5 13.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3l5 5"/><path d="M3 8h6"/></svg>',
    "recipes": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"/><line x1="6" y1="17" x2="18" y2="17"/></svg>',
    "products": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
    # 内页类型图标
    "concept": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "food": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>',
    "recipe": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"/></svg>',
    "guide": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    "product": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
    # 底部导航图标
    "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
}

# 顶级分类目录（用于侧边栏）
TOP_LEVEL_CATS = {"foods", "recipes", "products", "concepts", "community", "guides", "log"}

# 食材库的二级分类（在侧边栏中展开显示）
FOODS_SUBCATEGORIES = ["fruits", "grains", "legumes", "vegetables", "proteins"]

# 成品食品二级分类
PRODUCTS_SUBCATEGORIES = ["breads", "noodles", "snacks", "beverages", "condiments"]

# 食谱库二级分类
RECIPES_SUBCATEGORIES = ["breakfast", "main-meals", "snacks"]


class OKFPage:
    def __init__(self, filepath, lang):
        self.filepath = filepath
        self.lang = lang
        self.frontmatter = {}
        self.body_md = ""
        self.body_html = ""
        self.source_rel = ""
        self.url = ""
        self.url_depth = 0
        self._parse()
        self._compute_url()

    def _parse(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = f.read()
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                self.frontmatter = yaml.safe_load(parts[1]) or {}
                self.body_md = parts[2].strip()
            else:
                self.body_md = raw.strip()
        else:
            self.body_md = raw.strip()
        if not self.frontmatter.get("lang"):
            self.frontmatter["lang"] = self.lang

    def _compute_url(self):
        rel = os.path.relpath(self.filepath, CONTENT_DIR)
        no_ext = os.path.splitext(rel)[0]
        self.source_rel = no_ext

        path_parts = no_ext.split(os.sep)
        if path_parts[0] == self.lang:
            path_parts = path_parts[1:]
        is_index = os.path.basename(self.filepath) == "index.md"
        clean_parts = [p for p in path_parts if p and not (is_index and p == "index")]

        if not clean_parts:
            self.url = "/"
        else:
            self.url = "/" + "/".join(clean_parts) + "/"

        if self.lang != DEFAULT_LANG:
            self.url = "/" + self.lang + self.url

        raw_path = self.url
        self.url_depth = raw_path.rstrip("/").count("/") if raw_path != "/" else 0

    @property
    def type(self):
        return self.frontmatter.get("type", "")

    @property
    def title(self):
        return self.frontmatter.get("title", "")

    @property
    def description(self):
        return self.frontmatter.get("description", "")

    @property
    def tags(self):
        return self.frontmatter.get("tags", [])

    @property
    def updated_at(self):
        """OKF v0.2 generated.at, falling back to legacy v0.1 timestamp. Returns datetime or None."""
        generated = self.frontmatter.get("generated")
        value = generated.get("at", "") if isinstance(generated, dict) else ""
        if not value:
            value = self.frontmatter.get("timestamp", "")
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @property
    def sources(self):
        """OKF v0.2 sources list, falling back to legacy v0.1 single source string."""
        sources = self.frontmatter.get("sources")
        if isinstance(sources, list):
            return [s for s in sources if isinstance(s, dict) and s.get("resource")]
        legacy = self.frontmatter.get("source", "")
        return [{"resource": legacy}] if legacy else []

    @property
    def trust_tier(self):
        """OKF v0.2 §5.3: unverified / machine-confirmed / human-reviewed."""
        verified = self.frontmatter.get("verified")
        if isinstance(verified, dict):
            verified = [verified]
        if not isinstance(verified, list) or not verified:
            return ""
        actors = [str(v.get("by", "")) for v in verified if isinstance(v, dict)]
        return "human" if any(a.startswith("human:") for a in actors) else "machine"

    @property
    def is_stale(self):
        """OKF v0.2 §5.5: stale when today >= stale_after."""
        stale_after = self.frontmatter.get("stale_after")
        if isinstance(stale_after, datetime):
            stale_after = stale_after.date()
        if hasattr(stale_after, "year"):  # datetime.date
            return date.today() >= stale_after
        if isinstance(stale_after, str) and stale_after:
            try:
                return date.today() >= date.fromisoformat(stale_after)
            except ValueError:
                return False
        return False

    @property
    def is_index(self):
        return os.path.basename(self.filepath) == "index.md"

    @property
    def is_home(self):
        return self.is_index and os.path.dirname(self.filepath) == os.path.join(CONTENT_DIR, self.lang)

    def absolute_path(self):
        return "/" + "/".join(p for p in self.url.split("/") if p and p != self.lang) + "/"

    def __repr__(self):
        return f"<OKFPage {self.url} type={self.type}>"


class OKFBuild:
    def __init__(self):
        self.pages = []
        self.page_map = {}
        self.page_by_source = {}
        self.lang_versions = {}

    def collect_pages(self):
        for lang in os.listdir(CONTENT_DIR):
            lang_dir = os.path.join(CONTENT_DIR, lang)
            if not os.path.isdir(lang_dir) or lang.startswith("."):
                continue
            for root, _dirs, files in os.walk(lang_dir):
                for f in files:
                    if f.endswith(".md"):
                        fp = os.path.join(root, f)
                        page = OKFPage(fp, lang)
                        self.pages.append(page)
                        self.page_map[page.url] = page
                        self.page_by_source[page.source_rel] = page

        for p in self.pages:
            other_lang = "en" if p.lang == "zh" else "zh"
            counterpart_key = p.source_rel.replace(p.lang, other_lang, 1)
            counterpart = self.page_by_source.get(counterpart_key)
            if counterpart:
                self.lang_versions.setdefault(p, counterpart)
                self.lang_versions.setdefault(counterpart, p)

    def resolve_links(self, page):
        md = page.body_md
        
        # 自动列表生成功能：如果包含 {{AUTO_LIST}} 则自动生成目录列表
        if "{{AUTO_LIST}}" in md:
            auto_list = self._generate_auto_list(page)
            md = md.replace("{{AUTO_LIST}}", auto_list)

        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            title_attr = match.group(3) or ""

            url = url.strip()
            if url.startswith("http") or url.startswith("#") or url.startswith("mailto:"):
                return match.group(0)

            target = self._resolve_target(page, url)
            if target:
                correct_rel = self._relative_path(page.url, target.url)
                return f"[{text}]({correct_rel}{title_attr})"
            return match.group(0)

        md = re.sub(r'\[([^\]]*)\]\(([^)]*?)(\s+"[^"]*")?\)', replace_link, md)

        def replace_html_link(match):
            url = match.group(1)
            rest = match.group(2)
            if url.startswith("http") or url.startswith("#") or url.startswith("mailto:"):
                return match.group(0)
            target = self._resolve_target(page, url)
            if target:
                correct_rel = self._relative_path(page.url, target.url)
                return f'href="{correct_rel}"{rest}'
            return match.group(0)

        md = re.sub(r'href="([^"]*)"([^>]*)', replace_html_link, md)
        return md
    
    def _generate_auto_list(self, page):
        """自动扫描同目录下的所有 .md 文件，生成列表"""
        # 获取当前页面的目录路径
        source_dir = os.path.dirname(os.path.join(CONTENT_DIR, page.source_rel))
        
        if not os.path.isdir(source_dir):
            return "<!-- AUTO_LIST: 目录不存在 -->"
        
        # 扫描目录下的所有 .md 文件
        items = []
        for filename in os.listdir(source_dir):
            if not filename.endswith('.md') or filename == 'index.md':
                continue
            
            filepath = os.path.join(source_dir, filename)
            if not os.path.isfile(filepath):
                continue
            
            # 读取 frontmatter 获取标题
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析 YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        title = frontmatter.get('title', filename[:-3])
                        description = frontmatter.get('description', '')
                    else:
                        title = filename[:-3]
                        description = ''
                else:
                    title = filename[:-3]
                    description = ''
            except Exception as e:
                title = filename[:-3]
                description = ''
            
            # 生成相对链接
            rel_path = filename[:-3]  # 去掉 .md 后缀
            items.append({
                'title': title,
                'description': description,
                'url': rel_path
            })
        
        # 按标题排序
        items.sort(key=lambda x: x['title'])
        
        # 生成 markdown 列表
        if not items:
            return "<!-- AUTO_LIST: 没有找到任何项目 -->"
        
        lines = []
        for item in items:
            if item['description']:
                lines.append(f"- [{item['title']}]({item['url']}) — {item['description']}")
            else:
                lines.append(f"- [{item['title']}]({item['url']})")
        
        return '\n'.join(lines)

    def _resolve_target(self, page, url):
        if url.startswith("/"):
            target_url = url
        else:
            source_dir = os.path.dirname(page.source_rel)
            resolved = os.path.normpath(os.path.join(source_dir, url))
            target_page = self.page_by_source.get(resolved)
            if not target_page and resolved.endswith(".md"):
                target_page = self.page_by_source.get(resolved[:-3])
            if target_page:
                return target_page
            target_url = "/" + resolved + "/"
            if page.lang != DEFAULT_LANG:
                target_url = "/" + page.lang + target_url

        target = self.page_map.get(target_url)
        if not target and target_url.endswith("/"):
            target = self.page_map.get(target_url.rstrip("/"))
        if not target:
            if page.lang != DEFAULT_LANG and target_url.startswith("/" + page.lang):
                pass
            elif page.lang != DEFAULT_LANG:
                alt_url = "/" + page.lang + target_url
                target = self.page_map.get(alt_url)
        if not target and target_url.endswith("/"):
            prefix = target_url.rstrip("/")
            for p_url, p in self.page_map.items():
                if p_url.startswith(prefix + "/") and p_url != prefix + "/":
                    target = p
                    break
        return target

    def _relative_path(self, from_url, to_url):
        if from_url == to_url:
            return "."

        from_parts = [p for p in from_url.split("/") if p]
        to_parts = [p for p in to_url.split("/") if p]

        i = 0
        while i < len(from_parts) and i < len(to_parts) and from_parts[i] == to_parts[i]:
            i += 1

        ups = len(from_parts) - i
        if ups == 0 and from_url.endswith("/"):
            ups = len(from_parts) - i

        rel = [".."] * ups + to_parts[i:]
        if not rel:
            return "."
        return "/".join(rel) + "/"

    def build_nav_tree(self, lang):
        lang_pages = [p for p in self.pages if p.lang == lang and not p.is_home]
        tree = {}
        for p in lang_pages:
            parts = [part for part in p.url.split("/") if part and part != lang]
            current = tree
            for j, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_children": {}}
                if j == len(parts) - 1:
                    current[part]["_page"] = p
                current = current[part]["_children"]
        return tree

    def nav_to_html(self, tree, lang, current_url, level=0, parent_key=None):
        """生成简化版侧边栏导航
        
        规则：
        - level=0: 只显示一级分类入口
        - 食材库(foods): 展开显示二级分类（水果、谷物等），但不显示具体食物
        - 成品食品(products): 展开显示二级分类
        - 食谱库(recipes): 展开显示二级分类
        - 其他一级分类：不展开子分类
        - level>=2: 不显示（不显示具体食物/食谱）
        """
        # 二级及以上不显示（不显示具体食物）
        if level >= 2:
            return ""
        
        items = []
        
        # 定义一级分类的顺序
        category_order = ["community", "concepts", "foods", "guides", "log", "products", "recipes"]
        
        # 按顺序处理一级分类
        for key in category_order:
            if key not in tree:
                continue
                
            node = tree[key]
            page = node.get("_page")
            label = page.title if page else dir_label(key, lang)
            
            # 顶级分类显示图标
            icon = ""
            if key in SVG_ICONS:
                icon = f'<span class="nav-icon">{SVG_ICONS[key]}</span>'
            
            children = node.get("_children", {})
            has_children = bool(children)
            li_class = "nav-item"
            if has_children:
                li_class += " has-children"
            
            # 当前页面高亮
            is_current = current_url.startswith(f"/{lang}/{key}/") or current_url.startswith(f"/{key}/")
            if is_current:
                li_class += " current"

            # 生成链接
            if page:
                rel = self._relative_path(current_url, page.url)
                link = f'<a href="{rel}">{icon}<span class="nav-text">{escape(label)}</span></a>'
            else:
                link = f'<span class="nav-label">{icon}<span class="nav-text">{escape(label)}</span></span>'

            # 处理子分类
            children_html = ""
            if level == 0 and has_children:
                # 只展开特定分类的二级目录
                if key == "foods":
                    children_html = self._render_subcategories(children, FOODS_SUBCATEGORIES, lang, current_url, key)
                elif key == "products":
                    children_html = self._render_subcategories(children, PRODUCTS_SUBCATEGORIES, lang, current_url, key)
                elif key == "recipes":
                    children_html = self._render_subcategories(children, RECIPES_SUBCATEGORIES, lang, current_url, key)
                # 其他分类不展开

            items.append(f"<li class='{li_class}'>{link}{children_html}</li>")

        if items:
            return f"<ul class='nav-level-{level}'>{''.join(items)}</ul>"
        return ""
    
    def _render_subcategories(self, children, allowed_keys, lang, current_url, parent_key):
        """渲染指定的二级分类列表"""
        items = []
        for key in allowed_keys:
            if key not in children:
                continue
            node = children[key]
            page = node.get("_page")
            label = page.title if page else dir_label(key, lang)
            
            # 检查是否是当前页面
            is_current = current_url.startswith(f"/{lang}/{parent_key}/{key}/") or current_url.startswith(f"/{parent_key}/{key}/")
            li_class = "nav-item"
            if is_current:
                li_class += " current"
            
            if page:
                rel = self._relative_path(current_url, page.url)
                link = f'<a href="{rel}"><span class="nav-text">{escape(label)}</span></a>'
            else:
                link = f'<span class="nav-label"><span class="nav-text">{escape(label)}</span></span>'
            
            items.append(f"<li class='{li_class}'>{link}</li>")
        
        if items:
            return f"<ul class='nav-level-1'>{''.join(items)}</ul>"
        return ""

    def get_lang_switch_html(self, page):
        counterpart = self.lang_versions.get(page)
        others = [l for l in ["zh", "en"] if l != page.lang]
        result = ""
        for lang in others:
            label = "English" if lang == "en" else "中文"
            if counterpart:
                rel = self._relative_path(page.url, counterpart.url)
                result += f'<a href="{rel}" class="lang-link">{label}</a>'
            else:
                other_home = self._relative_path(page.url, "/en/" if lang == "en" else "/")
                result += f'<a href="{other_home}" class="lang-link">{label}</a>'
        return result

    def render_html(self, page):
        nav_html = self.nav_to_html(self.build_nav_tree(page.lang), page.lang, page.url)
        lang_switch = self.get_lang_switch_html(page)

        md_processed = self.resolve_links(page)
        page.body_html = markdown.markdown(
            md_processed,
            extensions=["extra", "toc", "sane_lists"],
        )

        tags_html = ""
        if page.tags:
            tag_items = "".join(f'<span class="tag">{escape(t)}</span>' for t in page.tags)
            tags_html = f'<div class="tags">{tag_items}</div>'

        is_home = page.is_home

        html = HTML_TEMPLATE.replace("{{LANG}}", page.lang)
        html = html.replace("{{SITE_URL}}", SITE_URL)
        html = html.replace("{{TITLE}}", escape(page.title) if page.title else ("低GI知识库" if page.lang == "zh" else "Low-GI Knowledge Base"))
        html = html.replace("{{DESC}}", escape(page.description) if page.description else "")
        html = html.replace("{{NAV}}", nav_html)
        html = html.replace("{{LANG_SWITCH}}", lang_switch)
        html = html.replace("{{LOGO_TEXT}}", "低GI知识库" if page.lang == "zh" else "Low-GI KB")
        html = html.replace("{{FOOTER_TEXT}}", "低GI社区知识库" if page.lang == "zh" else "Low-GI Community Knowledge Base")
        html = html.replace("{{HOME_LABEL}}", "首页" if page.lang == "zh" else "Home")
        html = html.replace("{{SEARCH_LABEL}}", "搜索" if page.lang == "zh" else "Search")
        html = html.replace("{{MENU_LABEL}}", "菜单" if page.lang == "zh" else "Menu")
        html = html.replace("{{SEARCH_PLACEHOLDER}}", "搜索食物、食谱、指南..." if page.lang == "zh" else "Search foods, recipes, guides...")
        
        # SVG图标替换
        for icon_name, icon_svg in SVG_ICONS.items():
            html = html.replace(f"{{{{SVG_ICONS[\"{icon_name}\"]}}}}", icon_svg)

        if is_home:
            body_html = self._render_home(page, tags_html)
        else:
            # 内页类型徽章（双语）
            TYPE_LABELS = {
                "zh": {"Food": "食材", "Recipe": "食谱", "Concept": "概念", "Guide": "指南",
                       "Product": "成品食品", "FAQ": "常见问题", "Product Category": "目录",
                       "Knowledge Base Home": "首页", "Log": "日志"},
                "en": {"Product Category": "Directory"},
            }
            type_label = TYPE_LABELS.get(page.lang, {}).get(page.type) or page.type.replace("_", " ").title()
            breadcrumb = self._breadcrumb(page)
            dt = page.updated_at
            date_html = f'<time datetime="{dt.isoformat()}">{dt.strftime("%Y-%m-%d")}</time>' if dt else ""
            # 正文首个 h1 与页头标题重复，去掉（移动端减少一屏内的重复标题）
            content_html = re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", page.body_html, count=1, flags=re.S)

            # OKF v0.2 信号：status / stale_after / verified / sources
            zh = page.lang == "zh"
            status = page.frontmatter.get("status", "")
            status_badge = ""
            if status == "draft":
                status_badge = f'<span class="status-badge draft">{"草稿" if zh else "Draft"}</span>'
            elif status == "deprecated":
                status_badge = f'<span class="status-badge deprecated">{"已废弃" if zh else "Deprecated"}</span>'
            tier = page.trust_tier
            verify_badge = ""
            if tier == "human":
                verify_badge = f'<span class="verify-badge human">{"✓ 已人工审核" if zh else "✓ Human-reviewed"}</span>'
            elif tier == "machine":
                verify_badge = f'<span class="verify-badge machine">{"已机器确认" if zh else "Machine-confirmed"}</span>'
            banner = ""
            if status == "deprecated":
                banner = f'<div class="stale-banner deprecated-banner">{"⚠️ 此内容已废弃，仅供参考，请不再依赖。" if zh else "⚠️ This content is deprecated and kept for reference only."}</div>'
            elif page.is_stale:
                banner = f'<div class="stale-banner">{"⚠️ 此内容可能已过期，请注意核实。" if zh else "⚠️ This content may be out of date."}</div>'

            sources_html = ""
            if page.sources:
                items = []
                for s in page.sources:
                    res = str(s.get("resource", ""))
                    label = escape(str(s.get("title", "") or res))
                    items.append(f'<li><a href="{escape(res)}">{label}</a></li>' if res.startswith("http") else f"<li>{label}</li>")
                sources_html = f'''<div class="page-sources">
                <h2>{"数据来源" if zh else "Sources"}</h2>
                <ul>{"".join(items)}</ul>
              </div>'''

            body_html = f"""
            <article class="content-page">
              <div class="page-header">
                <div class="type-badge">{escape(type_label)}</div>{status_badge}{verify_badge}
                <h1>{escape(page.title)}</h1>
                {tags_html}
                {breadcrumb}
                {f'<div class="page-meta">{("最后更新" if zh else "Updated")}: {date_html}</div>' if date_html else ''}
              </div>
              {banner}
              <div class="page-body">
                {content_html}
              </div>
              {sources_html}
            </article>
            """

        home_url = "/en/" if page.lang == "en" else "/"
        logo_href = self._relative_path(page.url, home_url)
        css_href = ASSET_BASE + "/assets/css/style.css"
        favicon_href = ASSET_BASE + "/assets/favicon.svg"
        search_base = self._relative_path(page.url, "/")
        if not search_base.endswith("/"):
            search_base += "/"
        html = html.replace("{{SEARCH_BASE}}", search_base)
        html = html.replace("{{LOGO_HREF}}", logo_href)
        html = html.replace("{{CSS_HREF}}", css_href)
        html = html.replace("{{FAVICON_HREF}}", favicon_href)
        html = html.replace("{{CONTENT}}", body_html)
        html = html.replace("{{YEAR}}", str(datetime.now().year))
        return html

    def _breadcrumb(self, page):
        raw_parts = [p for p in page.url.split("/") if p]
        parts = [p for p in raw_parts if p != page.lang]
        crumbs = []
        accumulated = "/" + page.lang + "/" if page.lang != DEFAULT_LANG else "/"
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                continue
            accumulated += part + "/"
            target = self.page_map.get(accumulated)
            if target:
                rel = self._relative_path(page.url, accumulated)
                label = dir_label(part, page.lang)
                crumbs.append(f'<a href="{rel}">{escape(label)}</a>')
        if crumbs:
            home_rel = self._relative_path(page.url, "/")
            home_text = "首页" if page.lang == "zh" else "Home"
            crumbs.insert(0, f'<a href="{home_rel}">{home_text}</a>')
        crumbs.append(f'<span class="current">{escape(page.title)}</span>')
        return '<nav class="breadcrumb">' + " › ".join(crumbs) + "</nav>"

    def _render_home(self, page, tags_html):
        logo_fallback = "低GI知识库" if page.lang == "zh" else "Low-GI Knowledge Base"
        return f"""
        <article class="home-page">
          <div class="hero">
            <h1>{escape(page.title) if page.title else logo_fallback}</h1>
            <p class="hero-desc">{escape(page.description) if page.description else ""}</p>
            {tags_html}
          </div>
          <div class="page-body">
            {page.body_html}
          </div>
        </article>
        """

    def write_site(self):
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)

        copied_pages = set()
        for page in self.pages:
            dst = os.path.join(OUTPUT_DIR, page.url.lstrip("/"), "index.html")
            dst = os.path.normpath(dst)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            html = self.render_html(page)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(html)
            copied_pages.add(page.url)

        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(OUTPUT_DIR, "assets")
        if os.path.exists(assets_src):
            if os.path.exists(assets_dst):
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)

        self._write_404()
        self._write_sitemap()
        if os.path.exists("robots.txt"):
            shutil.copy("robots.txt", os.path.join(OUTPUT_DIR, "robots.txt"))

        print(f"✅ 生成完成: {len(self.pages)} 页面 → {OUTPUT_DIR}/")

    def _write_404(self):
        # GitHub Pages renders 404.html at the requested (possibly deep) URL,
        # so every link and asset here must be absolute — relative paths break.
        nav_html_zh = self.nav_to_html(self.build_nav_tree("zh"), "zh", "/")
        nav_html_zh = nav_html_zh.replace('href="', f'href="{SITE_URL}/')
        body = """
        <div class="error-page" id="error-zh">
          <h1>404</h1>
          <p>页面未找到</p>
          <a href="__BASE__/" class="btn">返回首页</a>
        </div>
        <div class="error-page" id="error-en" style="display:none">
          <h1>404</h1>
          <p>Page Not Found</p>
          <a href="__BASE__/en/" class="btn">Back to Home</a>
        </div>
        <script>
        (function(){
          if (location.pathname.indexOf('/en/') !== -1) {
            document.getElementById('error-zh').style.display='none';
            document.getElementById('error-en').style.display='block';
          }
        })();
        </script>
        """.replace("__BASE__", SITE_URL)
        html = HTML_TEMPLATE
        html = html.replace("{{LANG}}", "zh")
        html = html.replace("{{LOGO_HREF}}", "./")
        html = html.replace("{{CSS_HREF}}", ASSET_BASE + "/assets/css/style.css")
        html = html.replace("{{FAVICON_HREF}}", ASSET_BASE + "/assets/favicon.svg")
        html = html.replace("{{SITE_URL}}", SITE_URL)
        html = html.replace("{{TITLE}}", "404 — Page Not Found")
        html = html.replace("{{DESC}}", "404 — Page Not Found")
        html = html.replace("{{NAV}}", nav_html_zh)
        html = html.replace("{{LANG_SWITCH}}", f'<a href="{SITE_URL}/en/" class="lang-link">English</a>')
        html = html.replace("{{LOGO_TEXT}}", "低GI知识库")
        html = html.replace("{{FOOTER_TEXT}}", "低GI社区知识库")
        html = html.replace("{{HOME_LABEL}}", "首页")
        html = html.replace("{{SEARCH_LABEL}}", "搜索")
        html = html.replace("{{MENU_LABEL}}", "菜单")
        # 404.html may be served at any path depth — search links must be absolute
        html = html.replace("{{SEARCH_BASE}}", SITE_URL + "/")
        html = html.replace("{{CONTENT}}", body)
        html = html.replace("{{YEAR}}", str(datetime.now().year))
        with open(os.path.join(OUTPUT_DIR, "404.html"), "w", encoding="utf-8") as f:
            f.write(html)

    def _write_sitemap(self):
        urls = []
        for page in self.pages:
            dt = page.updated_at
            lastmod = f"<lastmod>{dt.strftime('%Y-%m-%d')}</lastmod>" if dt else ""
            urls.append(f"  <url><loc>{SITE_URL}{page.url}</loc>{lastmod}</url>")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml += "\n".join(urls)
        xml += "\n</urlset>\n"
        with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(xml)

    def check_links(self):
        errors = []
        for page in self.pages:
            html = self.render_html(page)
            # Skip pages with search input (homepages) as they have JS templates
            if 'search-input' in html:
                continue
            page_dir = os.path.join(OUTPUT_DIR, page.url.lstrip("/"))
            for m in re.finditer(r'<a\s+href="([^"]+)"', html):
                href = m.group(1)
                if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                    continue
                resolved = os.path.normpath(os.path.join(page_dir, href))
                if os.path.isdir(resolved):
                    resolved = os.path.join(resolved, "index.html")
                elif not resolved.endswith(".html"):
                    resolved = resolved + "/index.html"
                if not os.path.isfile(resolved):
                    errors.append(f"  {page.url:40s} → {href:40s}")
        if errors:
            print(f"\n❌ {len(errors)} broken link(s):\n" + "\n".join(errors))
            return False
        print("✅ All internal links are valid")
        return True


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<link rel="stylesheet" href="{{CSS_HREF}}">
<link rel="icon" href="{{FAVICON_HREF}}" type="image/svg+xml">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <button class="menu-toggle" aria-label="Toggle navigation">☰<span>{{MENU_LABEL}}</span></button>
    <a href="{{LOGO_HREF}}" class="logo">{{LOGO_TEXT}}</a>
    <div class="header-actions">
      <button class="search-toggle" id="search-toggle" aria-label="Search">{{SVG_ICONS["search"]}}</button>
      <nav class="lang-nav">
        {{LANG_SWITCH}}
      </nav>
    </div>
  </div>
</header>

<!-- Global Search Modal -->
<div class="search-modal" id="search-modal">
  <div class="search-modal-backdrop"></div>
  <div class="search-modal-content">
    <div class="search-input-wrapper">
      <span class="search-icon">{{SVG_ICONS["search"]}}</span>
      <input type="text" class="search-input" id="global-search-input" placeholder="{{SEARCH_PLACEHOLDER}}" autocomplete="off">
      <button class="search-close" id="search-close" aria-label="Close">&times;</button>
    </div>
    <div class="search-results" id="global-search-results"></div>
  </div>
</div>

<div class="layout">
  <div class="sidebar-overlay" id="sidebar-overlay"></div>
  <aside class="sidebar" id="sidebar">
    <nav class="sidebar-nav">
      {{NAV}}
    </nav>
  </aside>
  <main class="main-content">
    {{CONTENT}}
  </main>
</div>
<script>
(function(){
  var btn = document.querySelector('.menu-toggle');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  function toggle(){ sidebar.classList.toggle('open'); overlay.classList.toggle('show'); }
  btn.addEventListener('click', toggle);
  overlay.addEventListener('click', toggle);
})();

/* Global Search Modal functionality */
(function(){
  var searchToggle = document.getElementById('search-toggle');
  var searchModal = document.getElementById('search-modal');
  var searchClose = document.getElementById('search-close');
  var searchInput = document.getElementById('global-search-input');
  var searchResults = document.getElementById('global-search-results');
  var backdrop = searchModal.querySelector('.search-modal-backdrop');
  
  if (!searchToggle || !searchModal) return;
  
  var isZh = document.documentElement.lang === 'zh';
  var langPrefix = isZh ? '' : 'en/';
  var searchBase = '{{SEARCH_BASE}}';  // relative path from current page to site root
  
  // Full page index for global search
  var pageIndex = isZh ? [
    // 核心概念
    {t:'血糖生成指数 (GI)', d:'GI是衡量食物引起血糖升高程度的指标', u:'concepts/glycemic-index/', type:'概念', cat:'concepts'},
    {t:'血糖负荷 (GL)', d:'GL综合考虑GI和份量，更准确评估食物对血糖的影响', u:'concepts/glycemic-load/', type:'概念', cat:'concepts'},
    {t:'胰岛素指数 (II)', d:'II衡量食物引起胰岛素分泌的程度', u:'concepts/insulin-index/', type:'概念', cat:'concepts'},
    {t:'膳食纤维', d:'纤维对血糖控制和消化健康的重要性', u:'concepts/dietary-fiber/', type:'概念', cat:'concepts'},
    // 食材库 - 谷物
    {t:'燕麦片', d:'低GI谷物，富含β-葡聚糖，有助于控制血糖', u:'foods/grains/rolled-oats/', type:'谷物', cat:'foods'},
    {t:'糙米', d:'全谷物，GI比白米低，富含纤维', u:'foods/grains/brown-rice/', type:'谷物', cat:'foods'},
    {t:'藜麦', d:'高蛋白假谷物，GI低，含完整氨基酸', u:'foods/grains/quinoa/', type:'谷物', cat:'foods'},
    {t:'全麦面包', d:'比白面包GI更低，富含纤维', u:'foods/grains/whole-wheat-bread/', type:'谷物', cat:'foods'},
    {t:'荞麦', d:'低GI谷物，适合糖尿病患者', u:'foods/grains/buckwheat/', type:'谷物', cat:'foods'},
    {t:'黑米', d:'抗氧化谷物，富含花青素', u:'foods/grains/black-rice/', type:'谷物', cat:'foods'},
    // 食材库 - 豆类
    {t:'鹰嘴豆', d:'高蛋白高纤维豆类，GI极低', u:'foods/legumes/chickpeas/', type:'豆类', cat:'foods'},
    {t:'扁豆', d:'低GI豆类，富含蛋白质和纤维', u:'foods/legumes/lentils/', type:'豆类', cat:'foods'},
    {t:'黑豆', d:'高蛋白豆类，富含抗氧化剂', u:'foods/legumes/black-beans/', type:'豆类', cat:'foods'},
    // 食材库 - 水果
    {t:'苹果', d:'纤维丰富的水果，GI低，含果胶', u:'foods/fruits/apple/', type:'水果', cat:'foods'},
    {t:'蓝莓', d:'抗氧化浆果，GI低，富含花青素', u:'foods/fruits/blueberry/', type:'水果', cat:'foods'},
    {t:'草莓', d:'低糖水果，富含维生素C', u:'foods/fruits/strawberry/', type:'水果', cat:'foods'},
    {t:'梨', d:'水分丰富，膳食纤维含量高，低GI水果', u:'foods/fruits/pear/', type:'水果', cat:'foods'},
    {t:'柚子', d:'低GI柑橘类水果', u:'foods/fruits/grapefruit/', type:'水果', cat:'foods'},
    {t:'樱桃', d:'低GI水果，含天然褪黑素', u:'foods/fruits/cherry/', type:'水果', cat:'foods'},
    // 食材库 - 蔬菜
    {t:'西兰花', d:'十字花科蔬菜，GI极低，富含维生素C', u:'foods/vegetables/broccoli/', type:'蔬菜', cat:'foods'},
    {t:'菠菜', d:'绿叶蔬菜，对血糖影响极小', u:'foods/vegetables/spinach/', type:'蔬菜', cat:'foods'},
    {t:'羽衣甘蓝', d:'超级食物，营养密度极高', u:'foods/vegetables/kale/', type:'蔬菜', cat:'foods'},
    {t:'花椰菜', d:'低GI蔬菜，可替代米饭', u:'foods/vegetables/cauliflower/', type:'蔬菜', cat:'foods'},
    {t:'芦笋', d:'低GI蔬菜，富含叶酸', u:'foods/vegetables/asparagus/', type:'蔬菜', cat:'foods'},
    {t:'黄瓜', d:'水分丰富，GI极低', u:'foods/vegetables/cucumber/', type:'蔬菜', cat:'foods'},
    // 食材库 - 蛋白质
    {t:'鸡胸肉', d:'瘦蛋白，GI为零，增肌首选', u:'foods/proteins/chicken-breast/', type:'蛋白质', cat:'foods'},
    {t:'鸡蛋', d:'完整蛋白，GI极低，营养全面', u:'foods/proteins/egg/', type:'蛋白质', cat:'foods'},
    {t:'豆腐', d:'植物蛋白，GI低，富含异黄酮', u:'foods/proteins/tofu/', type:'蛋白质', cat:'foods'},
    {t:'三文鱼', d:'富含Omega-3的鱼类', u:'foods/proteins/salmon/', type:'蛋白质', cat:'foods'},
    {t:'希腊酸奶', d:'高蛋白酸奶，益生菌丰富', u:'foods/proteins/greek-yogurt/', type:'蛋白质', cat:'foods'},
    // 食谱库 - 早餐
    {t:'燕麦蓝莓碗', d:'高纤维早餐食谱，简单快捷', u:'recipes/breakfast/oatmeal-berry-bowl/', type:'早餐', cat:'recipes'},
    {t:'鸡蛋菠菜炒', d:'快手早餐食谱，高蛋白低GI', u:'recipes/breakfast/egg-and-spinach-scramble/', type:'早餐', cat:'recipes'},
    {t:'全麦吐司配牛油果', d:'健康脂肪早餐', u:'recipes/breakfast/avocado-toast/', type:'早餐', cat:'recipes'},
    // 食谱库 - 正餐
    {t:'烤鸡沙拉', d:'低GI正餐食谱，高蛋白', u:'recipes/main-meals/grilled-chicken-salad/', type:'正餐', cat:'recipes'},
    {t:'藜麦蔬菜碗', d:'素食正餐，营养均衡', u:'recipes/main-meals/quinoa-veggie-bowl/', type:'正餐', cat:'recipes'},
    {t:'三文鱼配芦笋', d:'Omega-3丰富的晚餐', u:'recipes/main-meals/salmon-asparagus/', type:'正餐', cat:'recipes'},
    // 食谱库 - 小食
    {t:'希腊酸奶芭菲', d:'健康小食食谱，益生菌丰富', u:'recipes/snacks/greek-yogurt-berry-parfait/', type:'小食', cat:'recipes'},
    {t:'鹰嘴豆泥', d:'高蛋白零食配蔬菜', u:'recipes/snacks/hummus-veggie/', type:'小食', cat:'recipes'},
    {t:'坚果混合', d:'健康脂肪零食', u:'recipes/snacks/trail-mix/', type:'小食', cat:'recipes'},
    // 成品食品
    {t:'低GI面包', d:'市售低GI面包推荐', u:'products/breads/', type:'成品', cat:'products'},
    {t:'低GI面条', d:'荞麦面、全麦面等', u:'products/noodles/', type:'成品', cat:'products'},
    {t:'健康零食', d:'低GI零食选择', u:'products/snacks/', type:'成品', cat:'products'},
    {t:'低糖饮品', d:'适合糖尿病患者的饮品', u:'products/beverages/', type:'成品', cat:'products'},
    // 实用指南
    {t:'如何读食品标签', d:'选购低GI食品的技巧', u:'guides/how-to-read-food-labels/', type:'指南', cat:'guides'},
    {t:'外出就餐指南', d:'餐厅点餐小技巧', u:'guides/dining-out-tips/', type:'指南', cat:'guides'},
    {t:'血糖监测指南', d:'如何监测和理解血糖数据', u:'guides/blood-sugar-monitoring/', type:'指南', cat:'guides'},
    {t:'低GI购物清单', d:'超市购物必备清单', u:'guides/shopping-list/', type:'指南', cat:'guides'},
    // 社区
    {t:'常见问题', d:'关于低GI饮食的FAQ', u:'community/faq/', type:'社区', cat:'community'},
    {t:'贡献指南', d:'如何为知识库做贡献', u:'community/contributing/', type:'社区', cat:'community'},
    // 更新日志
    {t:'更新日志', d:'网站更新记录', u:'log/', type:'日志', cat:'log'},
  ] : [
    // English index
    {t:'Glycemic Index (GI)', d:'GI measures how quickly a food raises blood sugar', u:'en/concepts/glycemic-index/', type:'Concept', cat:'concepts'},
    {t:'Glycemic Load (GL)', d:'GL considers both GI and serving size for accurate impact', u:'en/concepts/glycemic-load/', type:'Concept', cat:'concepts'},
    {t:'Insulin Index (II)', d:'II measures insulin response to foods', u:'en/concepts/insulin-index/', type:'Concept', cat:'concepts'},
    {t:'Dietary Fiber', d:'Importance of fiber for blood sugar control', u:'en/concepts/dietary-fiber/', type:'Concept', cat:'concepts'},
    {t:'Rolled Oats', d:'Low-GI grain rich in beta-glucan', u:'en/foods/grains/rolled-oats/', type:'Grain', cat:'foods'},
    {t:'Brown Rice', d:'Whole grain with lower GI than white rice', u:'en/foods/grains/brown-rice/', type:'Grain', cat:'foods'},
    {t:'Quinoa', d:'High-protein pseudograin, low GI', u:'en/foods/grains/quinoa/', type:'Grain', cat:'foods'},
    {t:'Whole Wheat Bread', d:'Lower GI than white bread', u:'en/foods/grains/whole-wheat-bread/', type:'Grain', cat:'foods'},
    {t:'Chickpeas', d:'High-protein, high-fiber legume, very low GI', u:'en/foods/legumes/chickpeas/', type:'Legume', cat:'foods'},
    {t:'Lentils', d:'Low-GI legume rich in protein', u:'en/foods/legumes/lentils/', type:'Legume', cat:'foods'},
    {t:'Apple', d:'Fiber-rich fruit with low GI', u:'en/foods/fruits/apple/', type:'Fruit', cat:'foods'},
    {t:'Blueberry', d:'Antioxidant-rich berry, low GI', u:'en/foods/fruits/blueberry/', type:'Fruit', cat:'foods'},
    {t:'Pear', d:'Water-rich fruit with plenty of fiber, low GI', u:'en/foods/fruits/pear/', type:'Fruit', cat:'foods'},
    {t:'Strawberry', d:'Low-sugar fruit rich in vitamin C', u:'en/foods/fruits/strawberry/', type:'Fruit', cat:'foods'},
    {t:'Broccoli', d:'Cruciferous vegetable, very low GI', u:'en/foods/vegetables/broccoli/', type:'Vegetable', cat:'foods'},
    {t:'Spinach', d:'Leafy green with minimal blood sugar impact', u:'en/foods/vegetables/spinach/', type:'Vegetable', cat:'foods'},
    {t:'Kale', d:'Nutrient-dense superfood', u:'en/foods/vegetables/kale/', type:'Vegetable', cat:'foods'},
    {t:'Chicken Breast', d:'Lean protein, zero GI', u:'en/foods/proteins/chicken-breast/', type:'Protein', cat:'foods'},
    {t:'Egg', d:'Complete protein, very low GI', u:'en/foods/proteins/egg/', type:'Protein', cat:'foods'},
    {t:'Tofu', d:'Plant-based protein, low GI', u:'en/foods/proteins/tofu/', type:'Protein', cat:'foods'},
    {t:'Salmon', d:'Omega-3 rich fish', u:'en/foods/proteins/salmon/', type:'Protein', cat:'foods'},
    {t:'Greek Yogurt', d:'High-protein yogurt with probiotics', u:'en/foods/proteins/greek-yogurt/', type:'Protein', cat:'foods'},
    {t:'Oatmeal Berry Bowl', d:'High-fiber breakfast recipe', u:'en/recipes/breakfast/oatmeal-berry-bowl/', type:'Breakfast', cat:'recipes'},
    {t:'Egg and Spinach Scramble', d:'Quick high-protein breakfast', u:'en/recipes/breakfast/egg-and-spinach-scramble/', type:'Breakfast', cat:'recipes'},
    {t:'Grilled Chicken Salad', d:'Low-GI main meal recipe', u:'en/recipes/main-meals/grilled-chicken-salad/', type:'Main Meal', cat:'recipes'},
    {t:'Quinoa Veggie Bowl', d:'Balanced vegetarian meal', u:'en/recipes/main-meals/quinoa-veggie-bowl/', type:'Main Meal', cat:'recipes'},
    {t:'Greek Yogurt Parfait', d:'Healthy snack with probiotics', u:'en/recipes/snacks/greek-yogurt-berry-parfait/', type:'Snack', cat:'recipes'},
    {t:'How to Read Food Labels', d:'Tips for choosing low-GI foods', u:'en/guides/how-to-read-food-labels/', type:'Guide', cat:'guides'},
    {t:'Dining Out Tips', d:'Restaurant ordering tips', u:'en/guides/dining-out-tips/', type:'Guide', cat:'guides'},
    {t:'FAQ', d:'Frequently asked questions about low-GI diet', u:'en/community/faq/', type:'Community', cat:'community'},
    {t:'Changelog', d:'Site update history', u:'en/log/', type:'Log', cat:'log'},
  ];
  
  function openModal() {
    searchModal.classList.add('show');
    document.body.style.overflow = 'hidden';
    setTimeout(function() { searchInput.focus(); }, 100);
  }
  
  function closeModal() {
    searchModal.classList.remove('show');
    document.body.style.overflow = '';
    searchInput.value = '';
    searchResults.classList.remove('show');
  }
  
  searchToggle.addEventListener('click', openModal);
  searchClose.addEventListener('click', closeModal);
  backdrop.addEventListener('click', closeModal);
  
  // Keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    // Cmd/Ctrl + K to open search
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openModal();
    }
    // ESC to close
    if (e.key === 'Escape' && searchModal.classList.contains('show')) {
      closeModal();
    }
  });
  
  // Search functionality
  var searchTimeout;
  searchInput.addEventListener('input', function(){
    clearTimeout(searchTimeout);
    var q = this.value.trim();
    if (q.length < 1) { 
      searchResults.innerHTML = '<div class="search-hint">' + (isZh ? '输入关键词搜索食物、食谱和指南...' : 'Type to search foods, recipes, and guides...') + '</div>';
      searchResults.classList.add('show');
      return; 
    }
    
    searchTimeout = setTimeout(function() {
      var qLower = q.toLowerCase();
      var hits = pageIndex.filter(function(p){
        return p.t.toLowerCase().indexOf(qLower) !== -1 || 
               p.d.toLowerCase().indexOf(qLower) !== -1 ||
               p.type.toLowerCase().indexOf(qLower) !== -1;
      }).slice(0, 10);

      if (hits.length === 0) {
        searchResults.innerHTML = '<div class="search-no-result">' + (isZh ? '未找到相关结果' : 'No results found') + '</div>';
      } else {
        searchResults.innerHTML = hits.map(function(p){
          return '<div class="search-result-item"><a href="' + searchBase + p.u + '"><div class="result-title">' + p.t + '</div><div class="result-meta"><span class="result-type">' + p.type + '</span><span class="result-desc">' + p.d.substring(0, 40) + '...</span></div></a></div>';
        }).join('');
      }
      searchResults.classList.add('show');
    }, 150);
  });
  
  // Show initial hint
  searchResults.innerHTML = '<div class="search-hint">' + (isZh ? '输入关键词搜索食物、食谱和指南...' : 'Type to search foods, recipes, and guides...') + '</div>';
})();

/* Mobile bottom nav (runs after DOM ready: the #bottom-nav div is rendered after this script) */
document.addEventListener('DOMContentLoaded', function(){
  var bn = document.getElementById('bottom-nav');
  if (!bn) return;
  bn.classList.add('show');

  var menuBtn = document.querySelector('.menu-toggle');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');

  var homeBtn = document.getElementById('bn-home');

  var searchBtn = document.getElementById('bn-search');
  if (searchBtn) {
    searchBtn.addEventListener('click', function(e){
      e.preventDefault();
      // Open global search modal
      var searchModal = document.getElementById('search-modal');
      var searchInput = document.getElementById('global-search-input');
      if (searchModal) {
        searchModal.classList.add('show');
        document.body.style.overflow = 'hidden';
        if (searchInput) setTimeout(function() { searchInput.focus(); }, 100);
      }
    });
  }

  var menuToggle = document.getElementById('bn-menu');
  if (menuToggle && menuBtn) {
    menuToggle.addEventListener('click', function(e){
      e.preventDefault();
      menuBtn.click();
    });
  }
});
</script>
<footer class="site-footer">
  <div class="footer-inner">
    <p>{{FOOTER_TEXT}} &copy; {{YEAR}} | <a href="https://github.com/thomaszta/lowgi-community.github.io">GitHub</a></p>
  </div>
</footer>
<div class="bottom-nav" id="bottom-nav">
  <a href="{{LOGO_HREF}}" id="bn-home"><span class="bn-icon">{{SVG_ICONS["home"]}}</span><span class="bn-label">{{HOME_LABEL}}</span></a>
  <a href="#" id="bn-search"><span class="bn-icon">{{SVG_ICONS["search"]}}</span><span class="bn-label">{{SEARCH_LABEL}}</span></a>
  <button id="bn-menu"><span class="bn-icon">{{SVG_ICONS["menu"]}}</span><span class="bn-label">{{MENU_LABEL}}</span></button>
</div>
</body>
</html>"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OKF Static Site Generator")
    parser.add_argument("--check-links", action="store_true", help="Check for broken internal links")
    args = parser.parse_args()

    build = OKFBuild()
    build.collect_pages()
    build.write_site()
    print("✅ 构建成功!")

    if args.check_links:
        ok = build.check_links()
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
