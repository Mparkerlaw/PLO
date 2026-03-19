"""Document drafting module — generate legal documents from templates."""

import os
import re
from datetime import datetime
from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "drafts"


def list_templates():
    """Return all available template names."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(f.stem for f in TEMPLATES_DIR.glob("*.md"))


def load_template(name):
    """Load a template file and return its contents."""
    filepath = TEMPLATES_DIR / f"{name}.md"
    if filepath.exists():
        return filepath.read_text()
    return None


def get_template_fields(name):
    """Extract all placeholder fields from a template.

    Placeholders use the format: {{field_name}}
    """
    content = load_template(name)
    if not content:
        return []
    return list(dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", content)))


def draft_document(template_name, fields):
    """Fill in a template with provided field values and save the draft.

    Args:
        template_name: Name of the template file (without .md).
        fields: Dict of {field_name: value} to fill in.

    Returns:
        Tuple of (output_path, content) or (None, error_message).
    """
    content = load_template(template_name)
    if not content:
        return None, f"Template '{template_name}' not found."

    # Replace all {{field}} placeholders
    for field, value in fields.items():
        content = content.replace(f"{{{{{field}}}}}", str(value))

    # Check for unfilled fields
    remaining = re.findall(r"\{\{(\w+)\}\}", content)
    if remaining:
        content += f"\n\n<!-- UNFILLED FIELDS: {', '.join(remaining)} -->"

    # Save draft
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{template_name}_{timestamp}.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(content)

    return str(output_path), content


def interactive_draft(template_name):
    """Interactively fill in a template by prompting for each field.

    Returns (output_path, content) or (None, error).
    """
    fields_list = get_template_fields(template_name)
    if not fields_list:
        content = load_template(template_name)
        if content is None:
            return None, f"Template '{template_name}' not found."
        return None, "Template has no fillable fields."

    print(f"\n— Drafting: {template_name} ({len(fields_list)} fields) —\n")
    fields = {}
    for field in fields_list:
        display = field.replace("_", " ").title()
        value = input(f"  {display}: ").strip()
        fields[field] = value if value else f"[{display}]"

    return draft_document(template_name, fields)
