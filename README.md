# 🌿 Low-GI Community Knowledge Base

An open-source, community-driven knowledge base for low glycemic index (GI) foods and recipes, designed to help people with diabetes access reliable, practical dietary guidance.

**[🌐 Browse the Knowledge Base →](https://thomaszta.github.io/lowgi-community.github.io/)**

## Features

- **Core Concepts** — Understand GI and GL and their role in diabetes management
- **Food Database** — Look up GI values and nutritional profiles for common foods
- **Recipe Collection** — Community-verified low-GI recipes with full nutritional analysis
- **Practical Guides** — Tips on shopping, cooking, and dining out
- **Built with OKF** — Follows the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog) v0.1 specification

## Languages

| Language | Code | Directory |
|----------|------|-----------|
| English | en | [`content/en/`](content/en/) |
| 中文 | zh | [`content/zh/`](content/zh/) |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Build the site
python build.py

# Build with link checking
python build.py --check-links

# Output goes to site/ directory
```

## How to Contribute

We welcome all forms of contribution! See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

- [Open an Issue](https://github.com/thomaszta/lowgi-community.github.io/issues/new/choose) to suggest new foods or report bugs
- Submit a Pull Request to add or update content
- All content follows OKF v0.1 frontmatter standards

## License

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
