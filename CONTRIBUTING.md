# Contributing Guide / 贡献指南

**English** | [中文](#贡献指南)

Thank you for considering contributing to the Low-GI Community Knowledge Base!

## Contribution Workflow

1. **Fork** this repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** under the `content/` directory
4. **Submit a Pull Request (PR)**

## File Standards (OKF Requirements)

All knowledge files must include YAML frontmatter (this site follows **OKF v0.2**):

- `type` — **Required**. e.g., `Food`, `Recipe`, `Concept`, `Guide`
- `title` — Recommended
- `description` — Recommended
- `tags` — Recommended (use English tags for cross-language search)
- `sources` — Recommended — list of origins the content derives from, each with a `resource` (legacy single-string `source` is still accepted)
- `generated` — Recommended — `{ by: human:your-name, at: <ISO 8601> }`, who/when produced the content (legacy `timestamp` is still accepted)
- `lang` — Recommended — language code, e.g., `zh`, `en`

Optional OKF v0.2 signals: `status` (`draft` / `stable` / `deprecated`), `stale_after` (`YYYY-MM-DD`, page shows an expiry notice on/after this date), `verified` (`{ by: human:reviewer, at: ... }`, page shows a trust badge).

### Example

```markdown
---
type: "Food"
title: "Rolled Oats"
description: "Minimally processed rolled oats, a classic low-GI staple."
tags: [grain, breakfast, low-GI, high-fiber]
sources:
  - resource: "References from Open Food Facts and Harvard T.H. Chan School of Public Health"
generated: { by: human:community, at: 2026-06-21T11:00:00Z }
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
  sources:
    - resource: "Based on product nutrition label"
  generated: { by: human:community, at: 2026-06-21T13:00:00Z }
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

### PR Labels

Type labels (`type: food`, `type: product`, `type: recipe`, `type: concept-guide`, `type: site`) and `lang: bilingual` are applied automatically based on changed files. Reviewers may add `lang: zh-only` / `lang: en-only` (translation needed), `status: needs-source` / `status: waiting-author` / `status: ready`, or close-as labels `r: spam` / `r: promotion` / `r: inaccurate-gi`.

---

## 贡献指南

感谢你考虑为低GI食谱知识库做出贡献！

## 贡献流程

1. **Fork** 本仓库
2. **创建分支**：`git checkout -b feature/your-feature-name`
3. 在 `content/` 目录下**修改或添加内容**
4. **提交 Pull Request (PR)**

## 文件规范（OKF 要求）

所有知识文件必须包含 YAML 元数据头（本站遵循 **OKF v0.2**）：

- `type` — **必须**，例如 `Food`、`Recipe`、`Concept`、`Guide`
- `title` — 推荐
- `description` — 推荐
- `tags` — 推荐（建议使用英文标签，便于跨语言检索）
- `sources` — 推荐，内容来源列表，每条含 `resource`（旧的单字符串 `source` 字段仍然兼容）
- `generated` — 推荐，`{ by: human:你的名字, at: <ISO 8601> }`，记录内容产生者与时间（旧的 `timestamp` 字段仍然兼容）
- `lang` — 推荐，语言代码，如 `zh`、`en`

OKF v0.2 可选信号：`status`（`draft` 草稿 / `stable` 稳定 / `deprecated` 已废弃）、`stale_after`（`YYYY-MM-DD`，到期后页面会显示过期提示）、`verified`（`{ by: human:审核人, at: ... }`，页面显示信任徽章）。

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
  sources:
    - resource: "参考产品包装营养标签"
  generated: { by: human:community, at: 2026-06-21T13:00:00Z }
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

## PR 标签说明

**自动打标**（按改动路径）：

| 标签 | 触发条件 |
|------|---------|
| `type: food` | 改动 `content/**/foods/**` |
| `type: product` | 改动 `content/**/products/**` |
| `type: recipe` | 改动 `content/**/recipes/**` |
| `type: concept-guide` | 改动 `content/**/concepts/**` 或 `content/**/guides/**` |
| `type: site` | 改动 `build.py`、`assets/`、`.github/` 等站点文件 |
| `lang: bilingual` | 中英内容同时改动 |

**审核者手动添加**：

| 标签 | 含义 |
|------|------|
| `type: fix` | 内容勘误（GI 值错误、链接失效等） |
| `lang: zh-only` / `lang: en-only` | 缺另一语言版本，待补译 |
| `status: needs-source` | 缺数据来源或来源不可靠 |
| `status: waiting-author` | 等待提交者修改 |
| `status: ready` | 审核通过，可合并 |
| `r: spam` / `r: promotion` / `r: inaccurate-gi` | 垃圾 PR / 含广告 / GI 值无法核实，直接关闭 |

## 审核流程

### 提交阶段

1. **自动化检查** - CI 会自动验证：
   - YAML 格式是否正确
   - 必填字段是否完整
   - GI 值是否在合理范围 (0-100)
   - 是否包含可疑内容（广告、链接等）

2. **人工审核** - 维护者会检查：
   - 数据来源是否可靠
   - GI 值是否准确
   - 内容是否符合社区标准

### 审核标准

**✅ 允许的内容：**
- 有可靠来源的食材 GI 数据
- 科学合理的食谱
- 正确的低GI概念解释

**❌ 不允许的内容：**
- 虚构的 GI 数据
- 高GI食品伪装成低GI
- 包含购买链接或联系方式
- 广告或推广内容
- 未经证实的健康声明

## 数据来源要求

⚠️ **重要**：所有 GI 数据必须注明来源！

**推荐的数据来源：**
- [Open Food Facts](https://world.openfoodfacts.org/)
- 哈佛大学公共卫生学院 (Harvard T.H. Chan School of Public Health)
- 中国食物成分表
- 学术期刊论文
- 官方营养数据库

**不建议使用的来源：**
- 未署名的"网传"数据
- 商业网站的营销内容
- 个人博客（除非有明确数据来源）

## GI 值分类标准

| 分类 | GI 范围 | 说明 |
|------|---------|------|
| 低GI | ≤ 55 | 血糖生成指数较低 |
| 中GI | 56-69 | 血糖生成指数中等 |
| 高GI | ≥ 70 | 血糖生成指数较高 |

## 内容质量检查清单

提交前请确认：

- [ ] GI 值来自可靠来源
- [ ] 已注明数据来源
- [ ] YAML 格式正确
- [ ] 必填字段完整
- [ ] 不包含广告或购买链接
- [ ] 内容客观、科学

## 常见问题

**Q: CI 检查失败怎么办？**
A: 查看 CI 日志中的错误信息，修复对应问题后重新提交。

**Q: 我不确定 GI 值怎么办？**
A: 可以提交 Issue 讨论，或者标注"GI值待确认"。

**Q: 可以提交高GI食品吗？**
A: 可以，但需要明确说明这是"高GI食品"而非"低GI食品"，帮助用户避坑。

---

## ⚠️ 免责声明

本知识库的内容仅供参考，不能替代专业医疗建议。
如有血糖控制需求，请咨询医生或营养师。

---

有问题？请提交 [Issue](https://github.com/thomaszta/lowgi-community.github.io/issues)

🙏 感谢你的贡献！
