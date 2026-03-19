# PLO Agent — Parker Law Office Assistant

A chat-based practice assistant for criminal defense and family law in Wisconsin.

## Quick Start

```bash
python run.py
```

Or:

```bash
python -m agent
```

## What It Does

- **Calendaring** — Track court dates, filing deadlines, hearings, and follow-ups with reminders
- **CCAP Monitoring** — Monitor your cases on Wisconsin Circuit Court Access for status changes
- **Client Intake** — Guided intake workflows for criminal defense and family law cases
- **Case Stage Tracking** — Know what tasks to complete at each stage of a case
- **Playbooks** — Quick access to your practice procedures and checklists

## Structure

```
agent/           — The PLO agent code
  chat.py        — Main chat interface
  calendar_mod.py — Calendar and deadline tracking
  ccap.py        — CCAP case monitoring
  workflows.py   — Criminal defense & family law workflows
  config.py      — Configuration and data management
playbooks/       — Step-by-step practice procedures
checklists/      — Quick-reference checklists
data/            — Local data (calendar events, monitored cases)
```

## Commands

| Command | What it does |
|---------|-------------|
| `calendar` | View upcoming events and reminders |
| `add event` | Add a court date or deadline |
| `cases` | List CCAP-monitored cases |
| `add case` | Start monitoring a case on CCAP |
| `check ccap` | Check all cases for updates |
| `intake` | Run client intake workflow |
| `stages` | View case stages and tasks |
| `playbook` | Read a practice playbook |
| `complete [id]` | Mark a calendar event as done |

## Roadmap — OpenClaw Agent

This is the foundation for an autonomous agent that can:

- [ ] AI-powered natural language chat (connect to Claude API)
- [ ] Automatic CCAP polling on a schedule
- [ ] Email/SMS deadline reminders
- [ ] Document drafting from templates
- [ ] Conflict checking across all cases

## Privacy

**Never commit client names, case details, or confidential information.** The `data/` directory is gitignored and stays local.
