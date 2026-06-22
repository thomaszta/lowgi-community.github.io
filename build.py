#!/usr/bin/env python3
"""
OKF → Static Site Generator
Reads OKF (Open Knowledge Format) markdown files and generates a clean static HTML site.
"""

import os
import re
import shutil
import json
from datetime import datetime
from pathlib import Path
from html import escape

import yaml
import markdown

SITE_URL = os.environ.get("SITE_URL", "https://thomaszta.github.io/lowgi-community.github.io")
CONTENT_DIR = "content"
OUTPUT_DIR = "site"
DEFAULT_LANG = "zh"

DIR_NAMES = {
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

TYPE_ICONS = {
    "Concept": "🧠",
    "Food": "🥗",
    "Food Category": "📁",
    "Recipe": "🍳",
    "Guide": "📖",
    "FAQ": "❓",
    "Product": "🏷️",
    "Product Category": "📁",
    "Knowledge Base Home": "🏠",
}


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

    def _resolve_target(self, page, url):
        if url.startswith("/"):
            target_url = url
        else:
            source_dir = os.path.dirname(page.source_rel)
            resolved = os.path.normpath(os.path.join(source_dir, url))
            target_page = self.page_by_source.get(resolved)
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

    def nav_to_html(self, tree, lang, current_url, level=0):
        items = []
        keys = sorted(tree.keys())
        for key in keys:
            node = tree[key]
            page = node.get("_page")
            label = DIR_NAMES.get(key, {}).get(lang, key)
            icon = ""
            if page and page.type in TYPE_ICONS:
                icon = TYPE_ICONS[page.type] + " "
            children = node.get("_children", {})
            has_children = bool(children)
            li_class = "nav-item"
            if has_children:
                li_class += " has-children"

            link = ""
            if page:
                rel = self._relative_path(current_url, page.url)
                link = f'<a href="{rel}">{icon}{escape(label)}</a>'
            elif has_children:
                link = f'<span class="nav-label">{icon}{escape(label)}</span>'
            else:
                link = f'<span class="nav-label">{icon}{escape(label)}</span>'

            children_html = ""
            if has_children:
                children_html = self.nav_to_html(children, lang, current_url, level + 1)

            items.append(f"<li class='{li_class}'>{link}{children_html}</li>")

        if items:
            return f"<ul class='nav-level-{level}'>{''.join(items)}</ul>"
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
        html = html.replace("{{TITLE}}", escape(page.title) if page.title else "低GI知识库")
        html = html.replace("{{DESC}}", escape(page.description) if page.description else "")
        html = html.replace("{{NAV}}", nav_html)
        html = html.replace("{{LANG_SWITCH}}", lang_switch)

        if is_home:
            body_html = self._render_home(page, tags_html)
        else:
            icon = TYPE_ICONS.get(page.type, "")
            type_label = page.type.replace("_", " ").title() if not page.type == "Product Category" else "目录"
            breadcrumb = self._breadcrumb(page)
            timestamp = page.frontmatter.get("timestamp", "")
            date_html = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    date_html = f'<time datetime="{timestamp}">{dt.strftime("%Y-%m-%d")}</time>'
                except:
                    pass

            body_html = f"""
            <article class="content-page">
              <div class="page-header">
                <div class="type-badge">{icon} {escape(type_label)}</div>
                <h1>{escape(page.title)}</h1>
                {tags_html}
                {breadcrumb}
                {f'<div class="page-meta">最后更新: {date_html}</div>' if date_html else ''}
              </div>
              <div class="page-body">
                {page.body_html}
              </div>
            </article>
            """

        home_url = "/en/" if page.lang == "en" else "/"
        logo_href = self._relative_path(page.url, home_url)
        css_href = SITE_URL + "/assets/css/style.css"
        favicon_href = SITE_URL + "/assets/favicon.ico"
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
                label = DIR_NAMES.get(part, {}).get(page.lang, part)
                crumbs.append(f'<a href="{rel}">{escape(label)}</a>')
        if crumbs:
            home_rel = self._relative_path(page.url, "/")
            crumbs.insert(0, f'<a href="{home_rel}">首页</a>')
        crumbs.append(f'<span class="current">{escape(page.title)}</span>')
        return '<nav class="breadcrumb">' + " › ".join(crumbs) + "</nav>"

    def _render_home(self, page, tags_html):
        return f"""
        <article class="home-page">
          <div class="hero">
            <h1>{escape(page.title) if page.title else "低GI社区知识库"}</h1>
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

        print(f"✅ 生成完成: {len(self.pages)} 页面 → {OUTPUT_DIR}/")

    def _write_404(self):
        html = HTML_TEMPLATE.replace("{{LANG}}", "zh")
        html = html.replace("{{LOGO_HREF}}", "./")
        html = html.replace("{{CSS_HREF}}", "assets/css/style.css")
        html = html.replace("{{FAVICON_HREF}}", "assets/favicon.ico")
        html = html.replace("{{SITE_URL}}", SITE_URL)
        html = html.replace("{{TITLE}}", "页面未找到")
        html = html.replace("{{DESC}}", "404 - 页面未找到")
        html = html.replace("{{NAV}}", self.nav_to_html(self.build_nav_tree("zh"), "zh", "/"))
        html = html.replace("{{LANG_SWITCH}}", '<a href="en/" class="lang-link">English</a>')
        html = html.replace("{{CONTENT}}", """
        <div class="error-page">
          <h1>404</h1>
          <p>页面未找到</p>
          <a href="./" class="btn">返回首页</a>
        </div>
        """)
        html = html.replace("{{YEAR}}", str(datetime.now().year))
        with open(os.path.join(OUTPUT_DIR, "404.html"), "w", encoding="utf-8") as f:
            f.write(html)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<link rel="stylesheet" href="{{CSS_HREF}}">
<link rel="icon" href="{{FAVICON_HREF}}" type="image/x-icon">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="{{LOGO_HREF}}" class="logo">低GI知识库</a>
    <nav class="lang-nav">
      {{LANG_SWITCH}}
    </nav>
  </div>
</header>
<div class="layout">
  <aside class="sidebar">
    <nav class="sidebar-nav">
      {{NAV}}
    </nav>
  </aside>
  <main class="main-content">
    {{CONTENT}}
  </main>
</div>
<footer class="site-footer">
  <div class="footer-inner">
    <p>低GI社区知识库 &copy; {{YEAR}} | <a href="https://github.com/thomaszta/lowgi-community.github.io">GitHub</a></p>
  </div>
</footer>
</body>
</html>"""


def main():
    build = OKFBuild()
    build.collect_pages()
    build.write_site()
    print("✅ 构建成功!")


if __name__ == "__main__":
    main()
