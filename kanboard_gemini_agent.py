#!/usr/bin/env python3
"""
kanboard_gemini_agent.py
Fetch tasks for one Kanboard project, classify them, ask Google Gemini for summary,
and send the report by email.
Requires: pip install google-genai requests python-dotenv
"""

from google import genai
from google.genai import Client
import os
import sys
import time
import base64
import logging
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from base64 import b64encode

# Load .env
load_dotenv()

# ---- Config from env ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KANBOARD_URL = os.getenv("KB_URL")
KANBOARD_USER = os.getenv("KB_USER")
KANBOARD_TOKEN = os.getenv("KB_TOKEN")
PROJECT_ID = int(os.getenv("KB_PROJECT_ID", "16"))

EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "ttc-prod.smtps.jp")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")  # comma-separated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kanboard-gemini-agent")

if not all([GEMINI_API_KEY, KANBOARD_URL, KANBOARD_USER, KANBOARD_TOKEN, PROJECT_ID, EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
    logger.error("Missing required environment variables. Exiting.")
    sys.exit(2)

# ---- Google GenAI Client ----
gemini_client = genai.Client(api_key="xxxxxxxxxxxxxxxxx")

client = Client(api_key="xxxxxxxxxxxxxxxxxxxxxxxxx")

# ---- Kanboard helper ----


def kb_headers():
    auth = f"{KANBOARD_USER}:{KANBOARD_TOKEN}"
    token = b64encode(auth.encode()).decode()
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {token}"
    }


def kb_call(method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "id": 1}
    if params:
        payload["params"] = params
    r = requests.post(KANBOARD_URL, json=payload,
                      headers=kb_headers(), timeout=30)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"Kanboard error: {j['error']}")
    return j.get("result")


def fetch_tasks(project_id):
    tasks = kb_call("getAllTasks", {"project_id": project_id})
    # Fetch column names if missing
    for t in tasks:
        if not t.get("column_name"):
            task_info = kb_call("getTask", {"task_id": t["id"]})
            t["column_name"] = task_info.get("column_title") or "Unknown"
    return tasks

# ---- Classification rules ----


def classify_tasks(tasks):
    wip_columns = ["work in progress", "dev",
                   "qc", "uat", "staging", "production"]
    blocked_columns = []  # Add blocked columns if any
    wip, blocked = [], []

    for t in tasks:
        col = (t.get("column_name") or "").strip().lower()
        if col in [c.lower() for c in wip_columns]:
            wip.append(t)
        elif col in [c.lower() for c in blocked_columns]:
            blocked.append(t)

    return wip, blocked

# ---- Build report text ----


def build_report_text(project_id, wip, blocked):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"Kanboard AI Report — Project {project_id}", f"Generated: {now}", ""]
    lines.append(
        f"Summary counts: InProgress={len(wip)}, Blocked={len(blocked)}\n")

    def section(title, items):
        lines.append(title + ":")
        if not items:
            lines.append("  None\n")
            return
        for t in items:
            due = t.get("date_due") and datetime.fromtimestamp(
                int(t["date_due"])).strftime("%Y-%m-%d") or "No due"
            lines.append(
                f"  - {t.get('title')} (id:{t.get('id')} | due:{due} | column:{t.get('column_name')})")
        lines.append("")

    section("Work In Progress", wip)
    section("Blocked / On Hold", blocked)
    return "\n".join(lines)

# ---- Gemini summarization ----
# ---- Gemini summarization ----


def gemini_summary(report_text):
    try:
        prompt = (
            "You are a project management assistant.\n"
            "Summarize the following Kanboard report in:\n"
            "1. 3 key risk points\n"
            "2. 3 recommended actions\n\n"
            " improvise tips for more productivity"
            f"{report_text}"
        )

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return f"Unable to generate Gemini summary. Error: {str(e)}"

# def gemini_summary(report_text):
#     prompt = (
#         "You are a project manager assistant. Given the Kanboard report below, "
#         "produce a 3-bullet summary of top risks and 3 recommended actions (concise). "
#         "Format as plain text.\n\nReport:\n" + report_text
#     )

#     try:
#         # Use the generative models API
#         model = client.models.get_model("gemini-2.5-flash")  # or "gemini-1.5-flash" for faster/cheaper
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         logger.error(f"Gemini API error: {e}")
#         # Fallback to a default response
#         return f"Unable to generate Gemini summary. Error: {str(e)}"
# def gemini_summary(report_text):
#     prompt = (
#         "You are a project manager assistant. Given the Kanboard report below, "
#         "produce a 3-bullet summary of top risks and 3 recommended actions (concise). "
#         "Format as plain text.\n\nReport:\n" + report_text
#     )

#     resp = client.chat.completions.create(
#         model="chat-bison-001",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.5,
#         max_output_tokens=400
#     )
#     return resp.choices[0].message.content

# ---- Save report locally ----


def save_report(report_text, summary_text=None, folder="reports"):
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder, f"kanboard_report_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        if summary_text:
            f.write("===== Gemini Summary =====\n")
            f.write(summary_text + "\n\n")
        f.write("===== Kanboard Raw Report =====\n")
        f.write(report_text)
    logger.info(f"Report saved locally: {filename}")
    return filename

# ---- Email ----


def send_email(subject, body_plain):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    part1 = MIMEText(body_plain, "plain")
    msg.attach(part1)
    s = smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=30)
    s.ehlo()
    if EMAIL_SMTP_PORT == 587:
        s.starttls()
    s.login(EMAIL_USER, EMAIL_PASS)
    s.sendmail(EMAIL_USER, [x.strip()
               for x in EMAIL_TO.split(",")], msg.as_string())
    s.quit()
    logger.info("Email sent successfully")

# ---- Runner ----


def run(test_only=True):
    tasks = fetch_tasks(PROJECT_ID)
    wip, blocked = classify_tasks(tasks)
    plain = build_report_text(PROJECT_ID, wip, blocked)

    try:
        summary = gemini_summary(plain)
    except Exception as e:
        logger.exception("Gemini summarization failed")
        summary = None

    # Save report locally
    save_report(plain, summary)

    if test_only:
        print("===== Kanboard Raw Report =====")
        print(plain)
        if summary:
            print("\n===== Gemini Summary =====")
            print(summary)
        return

    # Send email
    body = f"Gemini summary:\n\n{summary}\n\n---\n\n{plain}" if summary else plain
    subject = f"Kanboard Report - Project {PROJECT_ID}"
    send_email(subject, body)
    logger.info("Report sent: WIP=%d Blocked=%d", len(wip), len(blocked))


if __name__ == "__main__":
    run(test_only=False)  # Set to False to send email

