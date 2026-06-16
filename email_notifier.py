"""
email_notifier.py
-------------------
Sends the standup summary report to the Project Lead via email.

To use Gmail:
1. Turn on 2-Step Verification: Google Account -> Security
2. Generate an "App Password" (16-character password)
3. Use that app password as SENDER_PASSWORD (not your normal Gmail password)

Environment variables (recommended, do not hardcode credentials):
    STANDUP_EMAIL_SENDER=youraddress@gmail.com
    STANDUP_EMAIL_PASSWORD=your_app_password
    STANDUP_EMAIL_RECEIVER=projectlead@example.com
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def build_email_body(report: dict) -> str:
    """report dict (standup_core.build_report() output) -> HTML email body."""
    blockers_html = report["blockers"].to_html(index=False) if not report["blockers"].empty else "<p>No blockers 🎉</p>"
    pending_html = report["pending"].to_html(index=False) if not report["pending"].empty else "<p>No pending work.</p>"
    followups_html = report["followups"].to_html(index=False) if not report["followups"].empty else "<p>No follow-ups needed.</p>"
    rec_html = "".join(f"<li>{r}</li>" for r in report["recommendations"])

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #2d2d2d;">
        <h2 style="color:#1a1a2e;">📋 Daily Standup Summary</h2>

        <h3>🧠 Overview</h3>
        <p>{report['summary']}</p>

        <h3>🚧 Blockers ({report['total_blockers']})</h3>
        {blockers_html}

        <h3>⏳ Pending Work</h3>
        {pending_html}

        <h3>📞 Follow-up Actions</h3>
        {followups_html}

        <h3>✅ Recommendations</h3>
        <ul>{rec_html}</ul>

        <hr>
        <p style="font-size:12px; color:#888;">
            Total members: {report['total_members']} |
            Total blockers: {report['total_blockers']} |
            Total follow-ups: {report['total_followups']}
        </p>
    </body>
    </html>
    """
    return html


def send_standup_email(report: dict,
                        sender_email: str = None,
                        sender_password: str = None,
                        receiver_email: str = None,
                        subject: str = "Daily Standup Summary"):
    """
    Sends the email. Credentials can be passed as arguments, or left
    as default to be read from environment variables.
    """
    sender_email = sender_email or os.environ.get("STANDUP_EMAIL_SENDER")
    sender_password = sender_password or os.environ.get("STANDUP_EMAIL_PASSWORD")
    receiver_email = receiver_email or os.environ.get("STANDUP_EMAIL_RECEIVER")

    if not all([sender_email, sender_password, receiver_email]):
        raise ValueError(
            "Email credentials missing. Set STANDUP_EMAIL_SENDER, "
            "STANDUP_EMAIL_PASSWORD, STANDUP_EMAIL_RECEIVER env vars, "
            "or pass them as arguments."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(build_email_body(report), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

    return True


if __name__ == "__main__":
    # Quick manual test
    import standup_core as core

    df = core.load_standup_data("standup.csv")
    report = core.build_report(df)

    try:
        send_standup_email(report)
        print("Email sent successfully!")
    except ValueError as e:
        print(f"Skipped sending (no credentials configured): {e}")
