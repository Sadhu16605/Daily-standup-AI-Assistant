"""
standup_assistant_v3.py
--------------------------
CLI entry point for the Daily Standup AI Assistant.
Uses standup_core.py for all logic (shared with Streamlit dashboard).

Usage:
    python standup_assistant_v3.py standup.csv
    python standup_assistant_v3.py standup.csv --llm        (use OpenAI summary)
    python standup_assistant_v3.py standup.csv --email       (send email after report)
"""

import sys
from tabulate import tabulate
import standup_core as core


def print_summary(report):
    print("\n" + "=" * 70)
    print(" DAILY STANDUP ASSISTANT — SUMMARY REPORT")
    print("=" * 70)

    print("\n🧠 OVERVIEW:")
    print("  " + report["summary"])

    print("\n🚧 BLOCKERS:")
    if report["blockers"].empty:
        print("  No blockers today! 🎉")
    else:
        print(tabulate(report["blockers"], headers='keys', tablefmt='grid', showindex=False))

    print("\n⏳ PENDING WORK:")
    if report["pending"].empty:
        print("  No pending work.")
    else:
        print(tabulate(report["pending"], headers='keys', tablefmt='grid', showindex=False))

    print("\n📞 FOLLOW-UP ACTIONS (for Project Lead to do):")
    if report["followups"].empty:
        print("  No follow-ups needed.")
    else:
        print(tabulate(report["followups"], headers='keys', tablefmt='grid', showindex=False))

    print("\n✅ RECOMMENDATIONS:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")

    print("\n" + "-" * 70)
    print(f" Total team members : {report['total_members']}")
    print(f" Total blockers      : {report['total_blockers']}")
    print(f" Total follow-ups    : {report['total_followups']}")
    print("-" * 70 + "\n")


def export_summary_to_html(report, output_path="standup_summary.html"):
    rec_html = "".join(f"<li>{r}</li>" for r in report["recommendations"])
    html = f"""
    <h2>Daily Standup Summary</h2>
    <h3>Overview</h3><p>{report['summary']}</p>
    <h3>Blockers</h3>{report['blockers'].to_html(index=False)}
    <h3>Pending Work</h3>{report['pending'].to_html(index=False)}
    <h3>Follow-up Actions</h3>{report['followups'].to_html(index=False)}
    <h3>Recommendations</h3><ul>{rec_html}</ul>
    """
    with open(output_path, "w") as f:
        f.write(html)
    print(f"HTML summary saved to: {output_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    csv_file = next((a for a in args if not a.startswith("--")), "standup.csv")
    use_llm = "--llm" in args
    send_email = "--email" in args

    data = core.load_standup_data(csv_file)
    report = core.build_report(data, use_llm=use_llm)

    print_summary(report)
    export_summary_to_html(report)

    if send_email:
        from email_notifier import send_standup_email
        try:
            send_standup_email(report)
            print("Email sent successfully!")
        except ValueError as e:
            print(f"Email not sent (missing credentials): {e}")
