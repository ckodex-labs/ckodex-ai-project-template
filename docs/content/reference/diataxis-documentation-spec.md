---
title: "Diátaxis Documentation Architecture & Dagger CI API Reference"
description: "Authoritative technical reference for the Diátaxis documentation taxonomy, Hugo layout contracts, and Dagger CI documentation pipeline API."
weight: 50
---

# Diátaxis Documentation Architecture & Dagger CI API Reference

This specification defines the structural taxonomy, layout contracts, frontmatter schemas, and build APIs governing documentation within the CKODEX platform.

---

## 1. Diátaxis Quadrant Taxonomy

Documentation is partitioned strictly across four directory roots according to the Diátaxis framework:

| Quadrant | Directory Path | Target Audience | Epistemic Mode | Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Tutorials** | `docs/content/tutorials/` | Newcomer | Learning | Practical, hands-on, step-by-step |
| **How-To Guides** | `docs/content/how-to/` | Practitioner | Problem-Solving | Goal-oriented, recipes, practical tasks |
| **Reference** | `docs/content/reference/` | Developer / Auditor | Information | Theoretical, specifications, schemas, tables |
| **Explanation** | `docs/content/explanation/` | Architect / Stakeholder | Understanding | Discursive, context, architectural rationale |

---

## 2. Frontmatter Schema Specification

Every Markdown file in `docs/content/` must declare YAML frontmatter adhering to the following schema:

```yaml
---
title: "Exact Title of the Document"        # string, required
description: "Single-sentence abstract."     # string, required (rendered in index lists)
weight: 10                                  # integer, required (ordering within parent section)
aliases:                                    # list of strings, optional (redirect URLs)
  - /old-path/
---
```

---

## 3. Hugo Configuration Reference (`docs/hugo.toml`)

```toml
baseURL = 'https://ckodex.cfyd.ai/'         # Overridden dynamically in CI via --baseURL
locale = 'en-us'
title = 'CKODEX AIOps Platform Documentation'

[params]
  description = "High-Assurance AI Architecture & DevSecOps Platform (Diátaxis Framework)"
  author = "CKODEX Core Engineering"
  version = "1.0.0"
  signature = "GAL 1 Constitutional"
  enableMermaid = true

[menu]
  [[menu.main]]
    identifier = "tutorials"
    name = "Tutorials"
    url = "/tutorials/"
    weight = 10
  [[menu.main]]
    identifier = "how-to"
    name = "How-To Guides"
    url = "/how-to/"
    weight = 20
  [[menu.main]]
    identifier = "reference"
    name = "Reference"
    url = "/reference/"
    weight = 30
  [[menu.main]]
    identifier = "explanation"
    name = "Explanation"
    url = "/explanation/"
    weight = 40
  [[menu.main]]
    identifier = "cockpit"
    name = "Mission Cockpit"
    url = "/cockpit.html"
    weight = 50
```

---

## 4. Dagger CI Documentation Engine API

Module: `ci/src/ckodex_cicd/main.py`

### Function: `build_docs`

```python
@function
def build_docs(
    self,
    source: dagger.Directory,
    base_url: str = "",
) -> dagger.Directory:
```

#### Parameters:
- `source` (`dagger.Directory`, required): Root repository directory containing the `docs/` subdirectory.
- `base_url` (`str`, optional): Base URL passed to Hugo via `--baseURL`. Defaults to empty string (uses `docs/hugo.toml` value).

#### Return:
- `dagger.Directory`: Hermetically compiled static HTML and asset directory (`docs/public`).

#### Container Execution:
- **Base Image**: `klakegg/hugo:ext-ubuntu`
- **Command**: `["hugo", "--destination", "/src/docs/public", "--cleanDestinationDir", ...]`
- **Caching**: Fully cached by Dagger's content-addressed execution graph.

---

## 5. Justfile Operational Interface

| Recipe | Synopsis | Command Invocation |
| :--- | :--- | :--- |
| `just docs-build` | Fast local static site compilation | `hugo --source docs --cleanDestinationDir` |
| `just docs-serve` | Local live-reload development server | `hugo server --source docs -D` |
| `just dagger-docs` | Containerized hermetic build via Dagger | `dagger call -m ./ci build-docs --source . export --path docs/public` |
| `just docs-pages-build` | Build site configured for GitHub Pages | `dagger call -m ./ci build-docs --source . --base-url <url> export --path docs/public` |
