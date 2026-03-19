"""Practice area workflows for criminal defense and family law."""

from pathlib import Path

PLAYBOOKS_DIR = Path(__file__).resolve().parent.parent / "playbooks"
CHECKLISTS_DIR = Path(__file__).resolve().parent.parent / "checklists"

# ── Criminal Defense Workflows ──────────────────────────────────────

CRIMINAL_INTAKE_QUESTIONS = [
    "What are the charges or allegations?",
    "What county was the case filed in?",
    "Do you have a case number (from CCAP or the complaint)?",
    "When is the next court date?",
    "Is the client currently in custody?",
    "Has the client made any statements to law enforcement?",
    "Are there any co-defendants?",
    "Is there a bond/bail amount set?",
]

CRIMINAL_CASE_STAGES = [
    "initial_appearance",
    "preliminary_hearing",
    "arraignment",
    "pretrial_motions",
    "plea_negotiations",
    "trial",
    "sentencing",
    "post_conviction",
]

# ── Family Law Workflows ────────────────────────────────────────────

FAMILY_INTAKE_QUESTIONS = [
    "What type of matter is this? (divorce, custody, child support, paternity, other)",
    "What county?",
    "Are there minor children involved?",
    "Is there an existing court order?",
    "Do you have a case number?",
    "Are there any safety concerns (domestic violence, restraining orders)?",
    "Is the other party represented by an attorney?",
    "What is the most urgent issue right now?",
]

FAMILY_CASE_STAGES = [
    "filing",
    "temporary_orders",
    "discovery",
    "mediation",
    "guardian_ad_litem",
    "pretrial",
    "trial",
    "post_judgment",
]

# ── Workflow Engine ─────────────────────────────────────────────────


def get_intake_questions(case_type):
    """Return intake questions for a case type."""
    if case_type == "criminal":
        return CRIMINAL_INTAKE_QUESTIONS
    elif case_type == "family":
        return FAMILY_INTAKE_QUESTIONS
    else:
        return CRIMINAL_INTAKE_QUESTIONS + FAMILY_INTAKE_QUESTIONS


def get_case_stages(case_type):
    """Return the progression of stages for a case type."""
    if case_type == "criminal":
        return CRIMINAL_CASE_STAGES
    elif case_type == "family":
        return FAMILY_CASE_STAGES
    return []


def get_stage_tasks(case_type, stage):
    """Return key tasks for a given case stage."""
    tasks = _STAGE_TASKS.get(case_type, {}).get(stage, [])
    return tasks


def load_playbook(name):
    """Load a playbook file by name and return its contents."""
    filepath = PLAYBOOKS_DIR / f"{name}.md"
    if filepath.exists():
        return filepath.read_text()
    return None


def load_checklist(name):
    """Load a checklist file by name and return its contents."""
    filepath = CHECKLISTS_DIR / f"{name}.md"
    if filepath.exists():
        return filepath.read_text()
    return None


# Key tasks by case type and stage
_STAGE_TASKS = {
    "criminal": {
        "initial_appearance": [
            "Review complaint and charges",
            "Argue bond/bail conditions",
            "Request discovery",
            "Calendar preliminary hearing date",
        ],
        "preliminary_hearing": [
            "Review discovery received",
            "Prepare cross-examination of state witnesses",
            "Evaluate bind-over standard",
            "Discuss plea options with client",
        ],
        "arraignment": [
            "Enter plea",
            "File any pretrial motions",
            "Calendar future dates",
        ],
        "pretrial_motions": [
            "File suppression motions if applicable",
            "File motions in limine",
            "Review state's witness list",
            "Prepare motion hearing arguments",
        ],
        "plea_negotiations": [
            "Review state's offer",
            "Discuss options and consequences with client",
            "Research sentencing guidelines",
            "Prepare counter-offer if applicable",
        ],
        "trial": [
            "Prepare jury instructions",
            "Finalize witness list and exhibits",
            "Prepare opening and closing statements",
            "Subpoena defense witnesses",
        ],
        "sentencing": [
            "Prepare sentencing memorandum",
            "Gather character references",
            "Research treatment/program options",
            "Prepare client for allocution",
        ],
        "post_conviction": [
            "Review appeal deadlines",
            "Evaluate grounds for post-conviction motion",
            "Calendar expungement eligibility date if applicable",
        ],
    },
    "family": {
        "filing": [
            "Prepare petition for filing",
            "Gather financial disclosure documents",
            "Determine if temporary orders are needed",
            "File and serve papers",
        ],
        "temporary_orders": [
            "Prepare motion for temporary orders",
            "Gather supporting affidavits",
            "Calendar hearing date",
            "Prepare proposed order",
        ],
        "discovery": [
            "Send interrogatories and document requests",
            "Review responses from opposing party",
            "Subpoena financial records if needed",
            "Calendar discovery deadlines",
        ],
        "mediation": [
            "Prepare mediation summary",
            "Outline client's priorities and goals",
            "Gather relevant documents for mediator",
            "Discuss BATNA with client",
        ],
        "guardian_ad_litem": [
            "Prepare client for GAL interview",
            "Provide relevant documents to GAL",
            "Calendar GAL report deadline",
        ],
        "pretrial": [
            "Prepare pretrial brief",
            "Finalize witness and exhibit lists",
            "Attend pretrial conference",
        ],
        "trial": [
            "Prepare testimony outlines",
            "Organize exhibits",
            "Prepare proposed findings of fact",
            "Prepare proposed custody/placement schedule",
        ],
        "post_judgment": [
            "Review modification grounds",
            "Calendar review dates",
            "Monitor compliance with court orders",
        ],
    },
}
