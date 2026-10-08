# AGENTS.md — Domain Content Manager Architecture & Rules

## Mission & Principles

`domain_content_manager` is a multi-domain, voice-first knowledge and content management system.

### Core Architectural Rules

1. **Workspace & Owner First**: Every content record must carry a `workspace_id` and `owner_id`.
2. **Voice-First**: All layers (Capture, Tagging, Retrieval, Output Generation) must support voice input (STT) and voice feedback (TTS).
3. **Obsidian Graph Integration**: All records are synced to an Obsidian Vault as Markdown files with rich YAML frontmatter and bidirectional `[[wikilinks]]`.
4. **Link Types**: Special bidirectional links (`derived_from`, `summary_of`, `infographic_of`, `related`) must be explicitly declared and synchronized between source material and generated summaries/infographics.
5. **Multi-Domain & Cross-Domain Schemas**: Support distinct schema fields for Health, Hair, Diet, Gardening, Foraging, Culinary, and general domains.
6. **Reliability & Risk Control**: Content records retain credibility ratings (`research`, `traditional`, `personal`, `doubt`) and risk levels (`none`, `low`, `medium`, `high`).
