"""AI chat module — Claude-powered conversational assistant for PLO.

Connects to the Anthropic API to provide intelligent, context-aware
responses about case management, deadlines, legal workflows, and more.
"""

import json
import os
from datetime import datetime

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from . import calendar_mod, ccap, workflows
from .config import load_json, CALENDAR_FILE, CASES_FILE

# System prompt that gives Claude full context about the practice
SYSTEM_PROMPT = """You are the PLO Agent, an AI assistant for Parker Law Office — a criminal defense and family law practice in Wisconsin.

You have access to the following tools and data:
- A calendar of court dates, deadlines, and events
- CCAP (Wisconsin Circuit Court Access) case monitoring
- Criminal defense and family law workflow knowledge
- Practice playbooks and checklists

Current date: {today}

CURRENT CALENDAR:
{calendar_summary}

MONITORED CASES:
{cases_summary}

PRACTICE AREAS:
- Criminal Defense: initial appearance → preliminary hearing → arraignment → pretrial motions → plea negotiations → trial → sentencing → post-conviction
- Family Law: filing → temporary orders → discovery → mediation → GAL → pretrial → trial → post-judgment

GUIDELINES:
- Be concise and practical
- When discussing cases, use only the reference names provided (never ask for or use real client names)
- If asked to do something you can't do yet, explain what capability is needed
- Proactively remind about upcoming deadlines when relevant
- For legal questions, provide general guidance but always note you are not a substitute for attorney judgment

You can help with:
1. Calendar management — "When is my next hearing?" "What's coming up this week?"
2. Case status — "Any CCAP updates?" "What's the status of case X?"
3. Workflow guidance — "What do I need to do for a preliminary hearing?" "Walk me through family law intake"
4. Practice questions — "What are the stages of a criminal case?" "What should I prepare for mediation?"
5. Task planning — "What should I prioritize today?" "What deadlines am I close to?"
"""

# Tools that Claude can call to take actions
TOOLS = [
    {
        "name": "get_upcoming_events",
        "description": "Get upcoming calendar events within a number of days",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 14)",
                }
            },
        },
    },
    {
        "name": "add_calendar_event",
        "description": "Add a new event to the calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_name": {"type": "string", "description": "Case reference name"},
                "event_type": {
                    "type": "string",
                    "enum": calendar_mod.EVENT_TYPES,
                    "description": "Type of event",
                },
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "description": {"type": "string", "description": "Brief description"},
                "remind_days": {
                    "type": "integer",
                    "description": "Days before to remind (default 3)",
                },
            },
            "required": ["case_name", "event_type", "date"],
        },
    },
    {
        "name": "check_ccap_cases",
        "description": "Check all monitored cases on CCAP for updates",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_case_stage_tasks",
        "description": "Get the tasks for a specific stage of a case type",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_type": {
                    "type": "string",
                    "enum": ["criminal", "family"],
                    "description": "Type of case",
                },
                "stage": {"type": "string", "description": "Stage name"},
            },
            "required": ["case_type", "stage"],
        },
    },
    {
        "name": "get_reminders",
        "description": "Get events that are within their reminder window",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "mark_event_complete",
        "description": "Mark a calendar event as completed",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID to mark complete"},
            },
            "required": ["event_id"],
        },
    },
]


def _build_system_prompt():
    """Build the system prompt with current data."""
    # Summarize calendar
    events = calendar_mod.get_upcoming(days=30)
    if events:
        cal_lines = []
        for e in events:
            cal_lines.append(
                f"- [{e['id']}] {e['date']} | {e['event_type']} | {e['case_name']} | {e.get('description', '')}"
            )
        calendar_summary = "\n".join(cal_lines)
    else:
        calendar_summary = "No upcoming events."

    # Summarize cases
    cases = ccap.list_cases()
    if cases:
        case_lines = []
        for c in cases:
            case_lines.append(
                f"- {c['case_number']} ({c['county']} Co.) | {c['case_name']} | {c['case_type']} | Status: {c.get('last_status', 'not checked')}"
            )
        cases_summary = "\n".join(case_lines)
    else:
        cases_summary = "No cases being monitored."

    return SYSTEM_PROMPT.format(
        today=datetime.now().strftime("%Y-%m-%d %A"),
        calendar_summary=calendar_summary,
        cases_summary=cases_summary,
    )


def _handle_tool_call(tool_name, tool_input):
    """Execute a tool call and return the result."""
    if tool_name == "get_upcoming_events":
        days = tool_input.get("days", 14)
        events = calendar_mod.get_upcoming(days)
        return json.dumps(events, default=str)

    elif tool_name == "add_calendar_event":
        event = calendar_mod.add_event(
            case_name=tool_input["case_name"],
            event_type=tool_input["event_type"],
            date_str=tool_input["date"],
            description=tool_input.get("description", ""),
            remind_days=tool_input.get("remind_days", 3),
        )
        return json.dumps(event, default=str)

    elif tool_name == "check_ccap_cases":
        results = ccap.check_all_cases()
        return json.dumps(results, default=str)

    elif tool_name == "get_case_stage_tasks":
        tasks = workflows.get_stage_tasks(
            tool_input["case_type"], tool_input["stage"]
        )
        return json.dumps(tasks)

    elif tool_name == "get_reminders":
        reminders = calendar_mod.get_reminders()
        return json.dumps(reminders, default=str)

    elif tool_name == "mark_event_complete":
        success = calendar_mod.mark_complete(tool_input["event_id"])
        return json.dumps({"success": success})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


class AIChat:
    """AI-powered chat session using Claude."""

    def __init__(self):
        self.conversation = []
        self.client = None
        self.model = "claude-sonnet-4-20250514"

        if not HAS_ANTHROPIC:
            return
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def available(self):
        return self.client is not None

    def chat(self, user_message):
        """Send a message and get a response, handling tool calls."""
        if not self.available:
            return self._fallback_response(user_message)

        self.conversation.append({"role": "user", "content": user_message})

        # Agentic loop — keep going until Claude gives a final text response
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=_build_system_prompt(),
                tools=TOOLS,
                messages=self.conversation,
            )

            # Collect the full response
            self.conversation.append({"role": "assistant", "content": response.content})

            # If no tool use, we're done
            if response.stop_reason != "tool_use":
                # Extract text from response
                text_parts = [
                    block.text for block in response.content if block.type == "text"
                ]
                return "\n".join(text_parts) if text_parts else "(No response)"

            # Handle tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Feed results back and let Claude continue
            self.conversation.append({"role": "user", "content": tool_results})

    def reset(self):
        """Clear conversation history."""
        self.conversation = []

    def _fallback_response(self, text):
        """Simple keyword response when API is not available."""
        lower = text.lower()
        if any(w in lower for w in ["deadline", "court", "hearing", "calendar", "when"]):
            events = calendar_mod.get_upcoming(14)
            if events:
                lines = ["Here are your upcoming events:"]
                for e in events:
                    lines.append(calendar_mod.format_event(e))
                return "\n".join(lines)
            return "No upcoming events in the next 14 days."
        elif any(w in lower for w in ["ccap", "case", "update", "status", "check"]):
            cases = ccap.list_cases()
            if cases:
                return f"You have {len(cases)} monitored cases. Use 'check ccap' to check for updates."
            return "No cases being monitored."
        elif any(w in lower for w in ["intake", "new client"]):
            return "Use 'intake criminal' or 'intake family' to start a guided intake."
        else:
            return (
                "AI chat requires an Anthropic API key.\n"
                "Set it with: export ANTHROPIC_API_KEY=your-key-here\n"
                "Then restart the agent.\n\n"
                "In the meantime, try commands like: calendar, cases, intake, stages"
            )
