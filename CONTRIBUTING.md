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

## Commercial Product Submissions

When adding a commercially available low-GI product:

- Use `type: "Product"` in the frontmatter
- Include the `brand` and `gi_value` fields
- Base nutritional data on the product's official nutrition label
- Note the purchase channel (e.g., supermarket, online retailer)
- Add to the correct category directory under `products/` (breads/, noodles/, snacks/, etc.)
- Example fields:
  ```yaml
  ---
  type: "Product"
  title: "Whole Wheat Bread"
  brand: "Brand Name"
  description: "Commercially available low-GI whole wheat bread."
  gi_value: "Approx. 50-55"
  tags: [bread, whole-grain, low-GI]
  purchase: "Available at major supermarkets"
  source: "Based on product nutrition label"
  timestamp: 2026-06-21T13:00:00Z
  lang: "en"
  ---
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

## 成品食品提交规范

添加市售低GI成品食品时：

- YAML 元数据使用 `type: "Product"`
- 必须包含 `brand`（品牌）和 `gi_value`（GI值估计）字段
- 营养数据以产品包装上的营养标签为准
- 注明购买渠道（超市、线上平台等）
- 放入 `products/` 下对应的分类目录（breads/、noodles/、snacks/ 等）
- 示例字段：
  ```yaml
  ---
  type: "Product"
  title: "全麦面包（某品牌）"
  brand: "品牌名称"
  description: "市售全麦面包，全麦粉含量≥50%。"
  gi_value: "约 50-55"
  tags: [面包, 全谷物, 低GI]
  purchase: "大型超市、线上电商平台有售"
  source: "参考产品包装营养标签"
  timestamp: 2026-06-21T13:00:00Z
  lang: "zh"
  ---
  ```

## 多语言指引

- 将内容放在对应的语言目录下：`content/en/`、`content/zh/` 等
- 不同语言版本的目录结构保持一致
- `type` 和 `tags` 字段在不同语言间保持一致
- 新增内容时尽量同时提供中英文版本
- 在同一语言内使用相对路径链接

## Pull Request 要求

- PR 标题清晰描述改动内容
- CI 检查通过后方可合并
