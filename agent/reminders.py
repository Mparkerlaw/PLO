"""Reminder module — send deadline alerts via email and/or SMS."""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from .config import DATA_DIR, ensure_data_dir

NOTIFY_CONFIG_FILE = DATA_DIR / "notify_config.json"


def load_notify_config():
    """Load notification configuration."""
    try:
        if NOTIFY_CONFIG_FILE.exists():
            return json.loads(NOTIFY_CONFIG_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return {
        "email": {"enabled": False, "smtp_host": "", "smtp_port": 587,
                   "username": "", "password": "", "from_addr": "", "to_addr": ""},
        "sms": {"enabled": False, "provider": "email_gateway",
                "phone": "", "gateway": ""},
    }


def save_notify_config(config):
    """Save notification configuration."""
    ensure_data_dir()
    NOTIFY_CONFIG_FILE.write_text(json.dumps(config, indent=2))


def configure_email(smtp_host, smtp_port, username, password, from_addr, to_addr):
    """Set up email notifications."""
    config = load_notify_config()
    config["email"] = {
        "enabled": True,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "username": username,
        "password": password,
        "from_addr": from_addr,
        "to_addr": to_addr,
    }
    save_notify_config(config)
    return True


def configure_sms(phone, carrier):
    """Set up SMS via carrier email gateway.

    Common carrier gateways:
        AT&T:      {number}@txt.att.net
        Verizon:   {number}@vtext.com
        T-Mobile:  {number}@tmomail.net
        Sprint:    {number}@messaging.sprintpcs.com
        US Cell:   {number}@email.uscc.net
    """
    gateways = {
        "att": "txt.att.net",
        "verizon": "vtext.com",
        "tmobile": "tmomail.net",
        "sprint": "messaging.sprintpcs.com",
        "uscellular": "email.uscc.net",
    }
    gateway = gateways.get(carrier.lower().replace("-", "").replace(" ", ""))
    if not gateway:
        return False, f"Unknown carrier: {carrier}. Supported: {', '.join(gateways.keys())}"

    config = load_notify_config()
    config["sms"] = {
        "enabled": True,
        "provider": "email_gateway",
        "phone": phone,
        "gateway": gateway,
    }
    save_notify_config(config)
    return True, f"SMS configured: {phone}@{gateway}"


def send_alert(alert_type, message):
    """Send an alert via all configured channels.

    Returns a dict of {channel: success_bool}.
    """
    config = load_notify_config()
    results = {}

    # Email
    if config.get("email", {}).get("enabled"):
        results["email"] = _send_email(
            config["email"], alert_type, message
        )

    # SMS (via email gateway)
    if config.get("sms", {}).get("enabled"):
        # SMS uses email config for SMTP, sends to phone gateway
        email_cfg = config.get("email", {})
        if email_cfg.get("smtp_host"):
            sms_cfg = config["sms"]
            sms_to = f"{sms_cfg['phone']}@{sms_cfg['gateway']}"
            results["sms"] = _send_email(
                email_cfg, alert_type, message, override_to=sms_to, short=True
            )
        else:
            results["sms"] = False  # Need email SMTP configured for SMS gateway

    return results


def _send_email(email_cfg, alert_type, message, override_to=None, short=False):
    """Send an email notification."""
    try:
        subject = f"PLO Alert: {alert_type.replace('_', ' ').title()}"
        to_addr = override_to or email_cfg["to_addr"]

        if short:
            # SMS — keep it brief
            body = message[:160]
        else:
            body = f"PLO Agent Alert\n{'='*40}\n\n{message}\n\n— PLO Agent"

        msg = MIMEMultipart()
        msg["From"] = email_cfg["from_addr"]
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as server:
            server.starttls()
            server.login(email_cfg["username"], email_cfg["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        return False


def get_notify_status():
    """Return a summary of notification configuration."""
    config = load_notify_config()
    lines = []
    email = config.get("email", {})
    if email.get("enabled"):
        lines.append(f"Email: ON → {email.get('to_addr', '?')}")
    else:
        lines.append("Email: OFF")

    sms = config.get("sms", {})
    if sms.get("enabled"):
        lines.append(f"SMS: ON → {sms.get('phone', '?')}@{sms.get('gateway', '?')}")
    else:
        lines.append("SMS: OFF")

    return "\n".join(lines)
