
import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date

# ── Config ──────────────────────────────────────────────────────────────────
GMAIL_USER = os.environ.get("GMAIL_USER", "civilbesafe@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT = os.environ.get("RECIPIENT_EMAIL", "civilbesafe@gmail.com")
CALENDAR_PATH = os.environ.get(
    "CALENDAR_PATH",
    "/a0/usr/projects/project_south_consultants/weekly_content_calendar.json"
)

# Campaign start date — Week 1
CAMPAIGN_START = date(2026, 3, 1)  # First Monday of campaign


def get_week_number() -> int:
    """Calculate current campaign week (1-52, then loops)."""
    today = date.today()
    delta = (today - CAMPAIGN_START).days
    week = (delta // 7) % 52 + 1
    return max(1, min(52, week))


def load_post(week: int) -> dict:
    with open(CALENDAR_PATH, encoding="utf-8") as f:
        calendar = json.load(f)
    for post in calendar:
        if post["week"] == week:
            return post
    return calendar[0]  # fallback to week 1


def build_email(post: dict, week: int) -> tuple[str, str]:
    topic = post["topic"]
    concept = post["concept"]
    fun_fact = post.get("fun_fact", "")
    linkedin = post.get("linkedin", "")
    reddit = post.get("reddit", "")
    facebook = post.get("facebook", "")
    terms = post.get("terms", {})

    terms_rows = "".join(
        f"<tr><td style='padding:6px 10px;border-bottom:1px solid #333;color:#aaa;'>{k}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #333;color:#fff;'>{v}</td></tr>"
        for k, v in terms.items()
    )

    def fmt_post(platform: str, emoji: str, content: str, color: str) -> str:
        safe = content.replace("
", "<br>").replace("'", "&#39;")
        return f"""
        <div style="margin:24px 0;background:#1a1a1a;border-radius:10px;overflow:hidden;">
          <div style="background:{color};padding:12px 20px;">
            <strong style="color:#fff;font-size:15px;">{emoji} {platform}</strong>
          </div>
          <div style="padding:20px;">
            <p style="color:#e0e0e0;line-height:1.7;white-space:pre-line;margin:0 0 16px 0;font-family:monospace;font-size:13px;">{safe}</p>
            <div style="background:#0a0a0a;border-radius:6px;padding:10px 14px;">
              <p style="color:#888;font-size:11px;margin:0;">📋 Copy the text above and paste directly into {platform}</p>
            </div>
          </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#0d0d0d;font-family:Arial,sans-serif;">
    <div style="max-width:680px;margin:0 auto;padding:20px;">

      <!-- Header -->
      <div style="background:linear-gradient(135deg,#1a3a5c,#0f2640);border-radius:12px;padding:30px;margin-bottom:24px;text-align:center;">
        <div style="font-size:36px;">🏗️</div>
        <h1 style="color:#fff;margin:10px 0 4px;font-size:22px;">Civil App Weekly Content</h1>
        <p style="color:#7eb8f7;margin:0;font-size:14px;">Week {week} of 52 &nbsp;|&nbsp; {datetime.now().strftime("%A %d %B %Y")}</p>
      </div>

      <!-- Topic Card -->
      <div style="background:#1a1a1a;border-radius:10px;padding:24px;margin-bottom:20px;border-left:4px solid #f59e0b;">
        <p style="color:#f59e0b;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">This Week's Topic</p>
        <h2 style="color:#fff;margin:0 0 8px;font-size:18px;">{topic}</h2>
        <p style="color:#aaa;margin:0;font-size:13px;">Concept: <strong style="color:#ddd;">{concept}</strong></p>
      </div>

      <!-- Fun Fact -->
      <div style="background:#1a1a1a;border-radius:10px;padding:20px;margin-bottom:20px;border-left:4px solid #10b981;">
        <p style="color:#10b981;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">💡 Did You Know?</p>
        <p style="color:#e0e0e0;margin:0;line-height:1.6;font-size:14px;">{fun_fact}</p>
      </div>

      <!-- Terms Table -->
      <div style="background:#1a1a1a;border-radius:10px;overflow:hidden;margin-bottom:24px;">
        <div style="background:#2a2a2a;padding:14px 20px;">
          <strong style="color:#fff;">🌍 International Terms Comparison</strong>
        </div>
        <table style="width:100%;border-collapse:collapse;">
          {terms_rows}
        </table>
      </div>

      <!-- Instructions -->
      <div style="background:#1c2a1a;border-radius:10px;padding:20px;margin-bottom:20px;border:1px solid #2d5a27;">
        <p style="color:#4ade80;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 10px;">📤 Your Posting Schedule This Week</p>
        <table style="width:100%;">
          <tr><td style="color:#aaa;padding:4px 0;">LinkedIn</td><td style="color:#fff;text-align:right;">Monday morning — best 8–10am</td></tr>
          <tr><td style="color:#aaa;padding:4px 0;">Reddit</td><td style="color:#fff;text-align:right;">Tuesday — r/heavyequipment + r/construction</td></tr>
          <tr><td style="color:#aaa;padding:4px 0;">Facebook</td><td style="color:#fff;text-align:right;">Wednesday — NZ/AU construction groups</td></tr>
        </table>
      </div>

      <!-- Platform Posts -->
      {fmt_post("LinkedIn", "💼", linkedin, "#0077b5")}
      {fmt_post("Reddit", "🟠", reddit, "#ff4500")}
      {fmt_post("Facebook", "📘", facebook, "#1877f2")}

      <!-- Footer -->
      <div style="text-align:center;padding:20px;color:#555;font-size:12px;">
        <p>🏗️ Civil App &nbsp;|&nbsp; South Consultants &nbsp;|&nbsp; civilbesafe@gmail.com</p>
        <p>Week {week}/52 &nbsp;•&nbsp; 52 weeks of civil construction content</p>
      </div>

    </div>
    </body></html>
    """

    plain = f"""CIVIL APP WEEKLY CONTENT — Week {week}/52
{datetime.now().strftime("%A %d %B %Y")}

TOPIC: {topic}
CONCEPT: {concept}

DID YOU KNOW?
{fun_fact}

{'='*60}
LINKEDIN POST (post Monday 8-10am):
{linkedin}

{'='*60}
REDDIT POST (post Tuesday):
{reddit}

{'='*60}
FACEBOOK POST (post Wednesday):
{facebook}

---
Civil App | South Consultants
"""
    return html, plain


def send_email(week: int = None):
    if week is None:
        week = get_week_number()

    print(f"📅 Loading Week {week} content...")
    post = load_post(week)
    html, plain = build_email(post, week)

    subject = f"🏗️ Civil App — Week {week}/52: {post['topic']}" 

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    if not GMAIL_APP_PASSWORD:
        print("⚠️  GMAIL_APP_PASSWORD not set — printing email instead")
        print(plain)
        return

    print(f"📧 Sending to {RECIPIENT}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())

    print(f"✅ Week {week} content emailed to {RECIPIENT}")
    print(f"   Topic: {post['topic']}")


if __name__ == "__main__":
    week_override = int(sys.argv[1]) if len(sys.argv) > 1 else None
    send_email(week_override)
