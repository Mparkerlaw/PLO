# PLO Agent — Parker Law Office Assistant

A chat-based practice assistant for criminal defense and family law in Wisconsin.
**OpenClaw Agent v0.2** — the foundation for an autonomous legal practice agent.

## Quick Start

```bash
# Install dependencies (optional, for AI chat)
pip install -r requirements.txt

# Set your API key for AI-powered chat (optional)
export ANTHROPIC_API_KEY=your-key-here

# Run the agent
python run.py
```

## Features

### Core
- **Calendaring** — Court dates, filing deadlines, hearings, and reminders
- **CCAP Monitoring** — Monitor cases on Wisconsin Circuit Court Access
- **Client Intake** — Guided workflows for criminal defense and family law
- **Case Stage Tracking** — Tasks for each phase of a case

### New in v0.2
- **AI Chat** — Claude-powered conversations about your cases, deadlines, and workflows. Ask questions naturally and the agent checks your calendar, CCAP, and workflow data to answer.
- **Auto CCAP Polling** — Background scheduler checks CCAP on a timer and alerts you when case statuses change.
- **Email/SMS Reminders** — Get deadline alerts sent to your email or phone via carrier gateway.
- **Document Drafting** — Generate engagement letters, motions, and client letters from templates with fill-in fields.

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
| `templates` | List available document templates |
| `draft` | Fill in and generate a document |
| `notify` | Configure email/SMS alerts |
| `scheduler start` | Start background CCAP polling |
| `logs` | View scheduler activity |
| `ai on/off` | Toggle AI chat mode |
| `complete [id]` | Mark a calendar event as done |

## Structure

```
agent/              — Python agent package
  chat.py           — Main chat interface and command routing
  ai_chat.py        — Claude API integration with tool use
  calendar_mod.py   — Calendar and deadline tracking
  ccap.py           — CCAP case monitoring
  workflows.py      — Criminal defense & family law workflows
  scheduler.py      — Background polling and alert scheduler
  reminders.py      — Email and SMS notification system
  drafter.py        — Document drafting engine
  config.py         — Configuration and data management
templates/          — Document templates (engagement letters, motions, etc.)
playbooks/          — Practice procedure guides
checklists/         — Quick-reference checklists
data/               — Local data (gitignored — calendar, cases, drafts)
```

## Document Templates

| Template | Use |
|----------|-----|
| `engagement-letter` | New client engagement/fee agreement |
| `motion-to-adjourn` | Request to reschedule a hearing |
| `client-letter` | General correspondence to clients |
| `custody-motion` | Motion to modify custody/placement |

Add your own templates to `templates/` using `{{field_name}}` placeholders.

## Privacy

**Never commit client names, case details, or confidential information.** The `data/` directory is gitignored and stays local only.
