# Contributing Guide / 贡献指南

**English** | [中文](#贡献指南)

Thank you for considering contributing to the Low-GI Community Knowledge Base!

## Contribution Workflow

1. **Fork** this repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** under the `content/` directory
4. **Submit a Pull Request (PR)**

## File Standards (OKF Requirements)

All knowledge files must include YAML frontmatter:

- `type` — **Required**. e.g., `Food`, `Recipe`, `Concept`, `Guide`
- `title` — Recommended
- `description` — Recommended
- `tags` — Recommended (use English tags for cross-language search)
- `source` — Recommended — cite your information sources
- `timestamp` — Recommended (ISO 8601 format)
- `lang` — Recommended — language code, e.g., `zh`, `en`

### Example

```markdown
---
type: "Food"
title: "Rolled Oats"
description: "Minimally processed rolled oats, a classic low-GI staple."
tags: [grain, breakfast, low-GI, high-fiber]
source: "References from Open Food Facts and Harvard T.H. Chan School of Public Health"
timestamp: 2026-06-21T11:00:00Z
lang: "en"
---

# Rolled Oats
```

## Multi-Language Guidelines

- Place content in the correct language directory: `content/en/`, `content/zh/`, etc.
- Keep the directory structure identical across all languages
- The `type` and `tags` fields should remain the same across languages
- When possible, provide both Chinese and English versions for new content
- Use relative links within the same language (e.g., `../concepts/glycemic-index.md`)

## Content Standards

- Cite information sources where possible
- Link to related entries within the knowledge base
- Keep content objective, science-based, and evidence-supported

## Pull Request Requirements

- Clear title describing the change
- CI checks must pass before merging

---

## 贡献指南

感谢你考虑为低GI食谱知识库做出贡献！

## 贡献流程

1. **Fork** 本仓库
2. **创建分支**：`git checkout -b feature/your-feature-name`
3. 在 `content/` 目录下**修改或添加内容**
4. **提交 Pull Request (PR)**

## 文件规范（OKF 要求）

所有知识文件必须包含 YAML 元数据头：

- `type` — **必须**，例如 `Food`、`Recipe`、`Concept`、`Guide`
- `title` — 推荐
- `description` — 推荐
- `tags` — 推荐（建议使用英文标签，便于跨语言检索）
- `source` — 推荐，注明信息来源
- `timestamp` — 推荐（ISO 8601 格式）
- `lang` — 推荐，语言代码，如 `zh`、`en`

## 多语言指引

- 将内容放在对应的语言目录下：`content/en/`、`content/zh/` 等
- 不同语言版本的目录结构保持一致
- `type` 和 `tags` 字段在不同语言间保持一致
- 新增内容时尽量同时提供中英文版本
- 在同一语言内使用相对路径链接

## Pull Request 要求

- PR 标题清晰描述改动内容
- CI 检查通过后方可合并
