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
from datetime import datetime
from pathlib import Path
from html import escape

import yaml
import markdown

SITE_URL = os.environ.get("SITE_URL", "https://thomaszta.github.io/lowgi-community.github.io")
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
            label = page.title if page else dir_label(key, lang)
            icon = ""
            if page and page.type in TYPE_ICONS:
                icon = TYPE_ICONS[page.type] + " "
            children = node.get("_children", {})
            has_children = bool(children)
            li_class = "nav-item"
            if has_children:
                li_class += " has-children"

            link = ""
            if page and not has_children:
                rel = self._relative_path(current_url, page.url)
                link = f'<a href="{rel}">{icon}{escape(label)}</a>'
            elif page and has_children:
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
        html = html.replace("{{TITLE}}", escape(page.title) if page.title else ("低GI知识库" if page.lang == "zh" else "Low-GI Knowledge Base"))
        html = html.replace("{{DESC}}", escape(page.description) if page.description else "")
        html = html.replace("{{NAV}}", nav_html)
        html = html.replace("{{LANG_SWITCH}}", lang_switch)
        html = html.replace("{{ROOT}}", "/" if page.lang == "zh" else "/en/")
        html = html.replace("{{LOGO_TEXT}}", "低GI知识库" if page.lang == "zh" else "Low-GI KB")
        html = html.replace("{{FOOTER_TEXT}}", "低GI社区知识库" if page.lang == "zh" else "Low-GI Community Knowledge Base")
        html = html.replace("{{HOME_LABEL}}", "首页" if page.lang == "zh" else "Home")
        html = html.replace("{{SEARCH_LABEL}}", "搜索" if page.lang == "zh" else "Search")
        html = html.replace("{{MENU_LABEL}}", "菜单" if page.lang == "zh" else "Menu")

        if is_home:
            body_html = self._render_home(page, tags_html)
        else:
            icon = TYPE_ICONS.get(page.type, "")
            type_label = page.type.replace("_", " ").title() if not page.type == "Product Category" else ("目录" if page.lang == "zh" else "Directory")
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
                {f'<div class="page-meta">{("最后更新" if page.lang == "zh" else "Updated")}: {date_html}</div>' if date_html else ''}
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
        nav_html_zh = self.nav_to_html(self.build_nav_tree("zh"), "zh", "/")
        nav_html_en = self.nav_to_html(self.build_nav_tree("en"), "en", "/en/")
        body = """
        <div class="error-page" id="error-zh">
          <h1>404</h1>
          <p>页面未找到</p>
          <a href="./" class="btn">返回首页</a>
        </div>
        <div class="error-page" id="error-en" style="display:none">
          <h1>404</h1>
          <p>Page Not Found</p>
          <a href="en/" class="btn">Back to Home</a>
        </div>
        <script>
        (function(){
          if (location.pathname.indexOf('/en/') !== -1) {
            document.getElementById('error-zh').style.display='none';
            document.getElementById('error-en').style.display='block';
          }
        })();
        </script>
        """
        html = HTML_TEMPLATE
        html = html.replace("{{LANG}}", "zh")
        html = html.replace("{{LOGO_HREF}}", "./")
        html = html.replace("{{CSS_HREF}}", "assets/css/style.css")
        html = html.replace("{{FAVICON_HREF}}", "assets/favicon.svg")
        html = html.replace("{{SITE_URL}}", SITE_URL)
        html = html.replace("{{TITLE}}", "404 — Page Not Found")
        html = html.replace("{{DESC}}", "404 — Page Not Found")
        html = html.replace("{{NAV}}", nav_html_zh)
        html = html.replace("{{LANG_SWITCH}}", '<a href="en/" class="lang-link">English</a>')
        html = html.replace("{{ROOT}}", "./")
        html = html.replace("{{LOGO_TEXT}}", "低GI知识库")
        html = html.replace("{{FOOTER_TEXT}}", "低GI社区知识库")
        html = html.replace("{{HOME_LABEL}}", "首页")
        html = html.replace("{{SEARCH_LABEL}}", "搜索")
        html = html.replace("{{MENU_LABEL}}", "菜单")
        html = html.replace("{{CONTENT}}", body)
        html = html.replace("{{YEAR}}", str(datetime.now().year))
        with open(os.path.join(OUTPUT_DIR, "404.html"), "w", encoding="utf-8") as f:
            f.write(html)

    def _write_sitemap(self):
        urls = []
        for page in self.pages:
            ts = page.frontmatter.get("timestamp", "")
            lastmod = ""
            if ts:
                try:
                    if isinstance(ts, datetime):
                        dt = ts
                    elif isinstance(ts, str):
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    else:
                        raise ValueError()
                    lastmod = f"<lastmod>{dt.strftime('%Y-%m-%d')}</lastmod>"
                except:
                    pass
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
    <a href="{{ROOT}}" class="logo">{{LOGO_TEXT}}</a>
    <nav class="lang-nav">
      {{LANG_SWITCH}}
    </nav>
  </div>
</header>
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

/* Search functionality */
(function(){
  var searchInput = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');
  if (!searchInput || !searchResults) return;

  var isZh = document.documentElement.lang === 'zh';

  var pageIndex = isZh ? [
    {t:'血糖生成指数 (GI)', d:'GI是衡量食物引起血糖升高程度的指标', u:'concepts/glycemic-index/', type:'概念'},
    {t:'血糖负荷 (GL)', d:'GL综合考虑GI和份量，更准确评估食物对血糖的影响', u:'concepts/glycemic-load/', type:'概念'},
    {t:'燕麦片', d:'低GI谷物，富含β-葡聚糖', u:'foods/grains/rolled-oats/', type:'食材'},
    {t:'糙米', d:'全谷物，GI比白米低', u:'foods/grains/brown-rice/', type:'食材'},
    {t:'藜麦', d:'高蛋白假谷物，GI低', u:'foods/grains/quinoa/', type:'食材'},
    {t:'鹰嘴豆', d:'高蛋白高纤维豆类，GI极低', u:'foods/legumes/chickpeas/', type:'食材'},
    {t:'苹果', d:'纤维丰富的水果，GI低', u:'foods/fruits/apple/', type:'食材'},
    {t:'蓝莓', d:'抗氧化 berries，GI低', u:'foods/fruits/blueberry/', type:'食材'},
    {t:'西兰花', d:'十字花科蔬菜，GI极低', u:'foods/vegetables/broccoli/', type:'食材'},
    {t:'菠菜', d:'绿叶蔬菜，对血糖影响极小', u:'foods/vegetables/spinach/', type:'食材'},
    {t:'鸡胸肉', d:'瘦蛋白，GI为零', u:'foods/proteins/chicken-breast/', type:'食材'},
    {t:'鸡蛋', d:'完整蛋白，GI极低', u:'foods/proteins/egg/', type:'食材'},
    {t:'豆腐', d:'植物蛋白，GI低', u:'foods/proteins/tofu/', type:'食材'},
    {t:'燕麦蓝莓碗', d:'高纤维早餐食谱', u:'recipes/breakfast/oatmeal-berry-bowl/', type:'食谱'},
    {t:'鸡蛋菠菜炒', d:'快手早餐食谱', u:'recipes/breakfast/egg-and-spinach-scramble/', type:'食谱'},
    {t:'烤鸡沙拉', d:'低GI正餐食谱', u:'recipes/main-meals/grilled-chicken-salad/', type:'食谱'},
    {t:'希腊酸奶芭菲', d:'健康小食食谱', u:'recipes/snacks/greek-yogurt-berry-parfait/', type:'食谱'},
    {t:'如何读食品标签', d:'选购低GI食品的技巧', u:'guides/how-to-read-food-labels/', type:'指南'},
    {t:'外出就餐指南', d:'餐厅点餐小技巧', u:'guides/dining-out-tips/', type:'指南'},
    {t:'常见问题', d:'关于低GI饮食的FAQ', u:'community/faq/', type:'社区'},
  ] : [
    {t:'Glycemic Index (GI)', d:'GI measures how quickly a food raises blood sugar', u:'en/concepts/glycemic-index/', type:'Concept'},
    {t:'Glycemic Load (GL)', d:'GL considers both GI and serving size for accurate impact', u:'en/concepts/glycemic-load/', type:'Concept'},
    {t:'Rolled Oats', d:'Low-GI grain rich in beta-glucan', u:'en/foods/grains/rolled-oats/', type:'Food'},
    {t:'Brown Rice', d:'Whole grain with lower GI than white rice', u:'en/foods/grains/brown-rice/', type:'Food'},
    {t:'Quinoa', d:'High-protein pseudograin, low GI', u:'en/foods/grains/quinoa/', type:'Food'},
    {t:'Chickpeas', d:'High-protein, high-fiber legume, very low GI', u:'en/foods/legumes/chickpeas/', type:'Food'},
    {t:'Apple', d:'Fiber-rich fruit with low GI', u:'en/foods/fruits/apple/', type:'Food'},
    {t:'Blueberry', d:'Antioxidant-rich berry, low GI', u:'en/foods/fruits/blueberry/', type:'Food'},
    {t:'Broccoli', d:'Cruciferous vegetable, very low GI', u:'en/foods/vegetables/broccoli/', type:'Food'},
    {t:'Spinach', d:'Leafy green with minimal blood sugar impact', u:'en/foods/vegetables/spinach/', type:'Food'},
    {t:'Chicken Breast', d:'Lean protein, zero GI', u:'en/foods/proteins/chicken-breast/', type:'Food'},
    {t:'Egg', d:'Complete protein, very low GI', u:'en/foods/proteins/egg/', type:'Food'},
    {t:'Tofu', d:'Plant-based protein, low GI', u:'en/foods/proteins/tofu/', type:'Food'},
    {t:'Oatmeal Berry Bowl', d:'High-fiber breakfast recipe', u:'en/recipes/breakfast/oatmeal-berry-bowl/', type:'Recipe'},
    {t:'Egg and Spinach Scramble', d:'Quick breakfast recipe', u:'en/recipes/breakfast/egg-and-spinach-scramble/', type:'Recipe'},
    {t:'Grilled Chicken Salad', d:'Low-GI main meal recipe', u:'en/recipes/main-meals/grilled-chicken-salad/', type:'Recipe'},
    {t:'Greek Yogurt Berry Parfait', d:'Healthy snack recipe', u:'en/recipes/snacks/greek-yogurt-berry-parfait/', type:'Recipe'},
    {t:'How to Read Food Labels', d:'Tips for choosing low-GI foods', u:'en/guides/how-to-read-food-labels/', type:'Guide'},
    {t:'Dining Out Tips', d:'Restaurant ordering tips', u:'en/guides/dining-out-tips/', type:'Guide'},
    {t:'FAQ', d:'Frequently asked questions about low-GI diet', u:'en/community/faq/', type:'Community'},
  ];

  searchInput.addEventListener('input', function(){
    var q = this.value.trim();
    if (q.length < 1) { searchResults.classList.remove('show'); return; }
    var qLower = q.toLowerCase();
    var hits = pageIndex.filter(function(p){
      return p.t.toLowerCase().indexOf(qLower) !== -1 || p.d.toLowerCase().indexOf(qLower) !== -1;
    }).slice(0, 8);

    if (hits.length === 0) {
      searchResults.innerHTML = '<div class="search-no-result">' + (isZh ? '未找到相关结果' : 'No results found') + '</div>';
    } else {
      searchResults.innerHTML = hits.map(function(p){
        return '<div class="search-result-item"><a href="' + p.u + '"><div class="result-title">' + p.t + '</div><div class="result-type">' + p.type + ' · ' + p.d.substring(0, 30) + '</div></a></div>';
      }).join('');
    }
    searchResults.classList.add('show');
  });

  document.addEventListener('click', function(e){
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
      searchResults.classList.remove('show');
    }
  });
})();

/* Mobile bottom nav */
(function(){
  var bn = document.getElementById('bottom-nav');
  if (!bn) return;
  bn.classList.add('show');

  var menuBtn = document.querySelector('.menu-toggle');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');

  var homeBtn = document.getElementById('bn-home');
  if (homeBtn) homeBtn.addEventListener('click', function(e){
    var root = document.documentElement.lang === 'zh' ? '/' : '/en/';
    if (location.pathname !== root && location.pathname !== root + 'index.html') {
      e.preventDefault();
      location.href = root;
    }
  });

  var searchBtn = document.getElementById('bn-search');
  if (searchBtn) searchBtn.addEventListener('click', function(e){
    e.preventDefault();
    var root = document.documentElement.lang === 'zh' ? '/' : '/en/';
    location.href = root + '#search-input';
  });

  var menuToggle = document.getElementById('bn-menu');
  if (menuToggle && menuBtn) {
    menuToggle.addEventListener('click', function(e){
      e.preventDefault();
      menuBtn.click();
    });
  }
})();
</script>
<footer class="site-footer">
  <div class="footer-inner">
    <p>{{FOOTER_TEXT}} &copy; {{YEAR}} | <a href="https://github.com/thomaszta/lowgi-community.github.io">GitHub</a></p>
  </div>
</footer>
<div class="bottom-nav" id="bottom-nav">
  <a href="{{ROOT}}" id="bn-home"><span class="bn-icon">🏠</span><span class="bn-label">{{HOME_LABEL}}</span></a>
  <a href="#" id="bn-search"><span class="bn-icon">🔍</span><span class="bn-label">{{SEARCH_LABEL}}</span></a>
  <button id="bn-menu"><span class="bn-icon">☰</span><span class="bn-label">{{MENU_LABEL}}</span></button>
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
