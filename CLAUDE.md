# CLAUDE.md — Instructions for Claude Code

## About This Repo

PLO Agent is the practice assistant for Parker Law Office. It's a chat-based tool for managing criminal defense and family law cases in Wisconsin.

## Structure

- `agent/` — Python package for the PLO agent
  - `chat.py` — Main chat loop and command routing
  - `calendar_mod.py` — Calendar, deadlines, and reminders
  - `ccap.py` — Wisconsin CCAP case monitoring
  - `workflows.py` — Criminal defense and family law intake/stage workflows
  - `config.py` — Data file management
- `playbooks/` — Markdown practice procedures
- `checklists/` — Markdown checklists
- `data/` — Local JSON data (gitignored, not committed)

## Running

```bash
python run.py
# or
python -m agent
```

## Guidelines

- All playbooks/checklists are written in Markdown
- Keep language plain and action-oriented (numbered steps, bullet points)
- Checklists use `- [ ]` checkbox format
- **NEVER include client names, case details, or confidential information in code or committed files**
- The `data/` directory is for local-only storage (calendar.json, cases.json)
- Practice areas: criminal defense and family law (Wisconsin)
- CCAP integration uses Wisconsin Circuit Court Access (wcca.wicourts.gov)
