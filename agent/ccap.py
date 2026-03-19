"""CCAP module — monitor Wisconsin Circuit Court Access for case updates."""

import json
import urllib.request
import urllib.error
from datetime import datetime

from .config import CASES_FILE, CCAP_SEARCH_URL, load_json, save_json


def add_case(case_name, county, case_number, case_type="criminal"):
    """Register a case to monitor on CCAP.

    Args:
        case_name: Display name (e.g. initials or case reference, NOT full client name).
        county: Wisconsin county (e.g. "Milwaukee", "Dane").
        case_number: CCAP case number (e.g. "2025CF001234").
        case_type: "criminal" or "family".

    Returns:
        The created case dict.
    """
    cases = load_json(CASES_FILE)
    case = {
        "case_name": case_name,
        "county": county,
        "case_number": case_number,
        "case_type": case_type,
        "added": datetime.now().isoformat(),
        "last_checked": None,
        "last_status": None,
    }
    # Avoid duplicates
    if any(c["case_number"] == case_number for c in cases):
        return None
    cases.append(case)
    save_json(CASES_FILE, cases)
    return case


def remove_case(case_number):
    """Stop monitoring a case."""
    cases = load_json(CASES_FILE)
    cases = [c for c in cases if c["case_number"] != case_number]
    save_json(CASES_FILE, cases)


def list_cases():
    """Return all monitored cases."""
    return load_json(CASES_FILE)


def check_ccap(county, case_number):
    """Query CCAP for a case and return the response.

    Returns a dict with case details or an error message.
    Note: CCAP may change their API; this uses their public JSON endpoint.
    """
    payload = json.dumps({
        "countyNo": _county_to_number(county),
        "caseNo": case_number,
    }).encode("utf-8")

    req = urllib.request.Request(
        CCAP_SEARCH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"status": "ok", "data": data}
    except urllib.error.HTTPError as e:
        return {"status": "error", "message": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"status": "error", "message": f"Connection failed: {e.reason}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_all_cases():
    """Check CCAP for all monitored cases and return results."""
    cases = load_json(CASES_FILE)
    results = []
    for case in cases:
        result = check_ccap(case["county"], case["case_number"])
        case["last_checked"] = datetime.now().isoformat()
        if result["status"] == "ok":
            new_status = _summarize_case(result["data"])
            changed = new_status != case.get("last_status")
            case["last_status"] = new_status
            results.append({
                "case_name": case["case_name"],
                "case_number": case["case_number"],
                "status": new_status,
                "changed": changed,
            })
        else:
            results.append({
                "case_name": case["case_name"],
                "case_number": case["case_number"],
                "error": result["message"],
                "changed": False,
            })
    save_json(CASES_FILE, cases)
    return results


def _summarize_case(data):
    """Extract a brief status string from CCAP response data."""
    if isinstance(data, dict):
        # Try common CCAP response fields
        status = data.get("status", "")
        next_date = data.get("nextCourtDate", "")
        charges = data.get("chargeCount", "")
        parts = []
        if status:
            parts.append(f"Status: {status}")
        if next_date:
            parts.append(f"Next date: {next_date}")
        if charges:
            parts.append(f"Charges: {charges}")
        return " | ".join(parts) if parts else json.dumps(data)[:200]
    return str(data)[:200]


# Wisconsin county name → CCAP county number mapping (partial — extend as needed)
_COUNTY_MAP = {
    "adams": 1, "ashland": 2, "barron": 3, "bayfield": 4, "brown": 5,
    "buffalo": 6, "burnett": 7, "calumet": 8, "chippewa": 9, "clark": 10,
    "columbia": 11, "crawford": 12, "dane": 13, "dodge": 14, "door": 15,
    "douglas": 16, "dunn": 17, "eau claire": 18, "florence": 19, "fond du lac": 20,
    "forest": 21, "grant": 22, "green": 23, "green lake": 24, "iowa": 25,
    "iron": 26, "jackson": 27, "jefferson": 28, "juneau": 29, "kenosha": 30,
    "kewaunee": 31, "la crosse": 32, "lafayette": 33, "langlade": 34, "lincoln": 35,
    "manitowoc": 36, "marathon": 37, "marinette": 38, "marquette": 39,
    "menominee": 40, "milwaukee": 41, "monroe": 42, "oconto": 43, "oneida": 44,
    "outagamie": 45, "ozaukee": 46, "pepin": 47, "pierce": 48, "polk": 49,
    "portage": 50, "price": 51, "racine": 52, "richland": 53, "rock": 54,
    "rusk": 55, "sauk": 56, "sawyer": 57, "shawano": 58, "sheboygan": 59,
    "st. croix": 60, "taylor": 61, "trempealeau": 62, "vernon": 63,
    "vilas": 64, "walworth": 65, "washburn": 66, "washington": 67,
    "waukesha": 68, "waupaca": 69, "waushara": 70, "winnebago": 71, "wood": 72,
}


def _county_to_number(county_name):
    """Convert county name to CCAP county number."""
    return _COUNTY_MAP.get(county_name.lower().strip(), 0)
