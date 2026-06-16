"""
standup_core.py
-----------------
Core logic for the Daily Standup Assistant — reusable by both the
CLI script (standup_assistant_v2.py) and the Streamlit dashboard
(streamlit_app.py).

Includes:
- CSV loading & cleaning
- Blocker detection (handles None/NA/N-A/-/Nil variations)
- Follow-up action generation
- Recommendation generation
- Rule-based AI summary (fallback)
- LLM-based AI summary (OpenAI) — optional, used if API key is set
"""

import pandas as pd
import re
import os

NO_BLOCKER_VALUES = {
    'none', 'na', 'n/a', '-', '--', 'nil', 'nothing',
    'no blocker', 'no blockers', 'no issues', 'not applicable', ''
}


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_standup_data(csv_path_or_buffer):
    """Load CSV (path or file-like object) and clean it."""
    df = pd.read_csv(csv_path_or_buffer)
    df['Blocker'] = df['Blocker'].fillna('None').astype(str).str.strip()
    df['Status'] = df['Status'].fillna('Unknown').astype(str).str.strip()
    df['Today'] = df['Today'].fillna('').astype(str).str.strip()
    df['Yesterday'] = df['Yesterday'].fillna('').astype(str).str.strip()
    return df


# ---------------------------------------------------------------------
# Blocker detection
# ---------------------------------------------------------------------

def has_real_blocker(blocker_text):
    cleaned = blocker_text.strip().lower()
    cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned not in NO_BLOCKER_VALUES and cleaned != ''


def get_blockers(df):
    mask = df['Blocker'].apply(has_real_blocker)
    return df[mask][['Name', 'Blocker']]


def get_pending_work(df):
    pending = df[df['Status'].str.lower() != 'done']
    return pending[['Name', 'Today', 'Status']]


# ---------------------------------------------------------------------
# Follow-up actions
# ---------------------------------------------------------------------

def extract_dependency_person(blocker_text):
    match = re.search(r'(?:waiting for|from|by)\s+([A-Z][a-zA-Z]+)', blocker_text)
    return match.group(1) if match else None


def generate_followup_action(name, blocker_text):
    text = blocker_text.strip().rstrip('.')
    lower = text.lower()
    dep_person = extract_dependency_person(text)

    if dep_person:
        return f"Follow up with {dep_person} to unblock {name}'s task (related to: {text.lower()})."
    elif 'approval' in lower or 'access' in lower:
        return f"Follow up with {name} regarding {text.lower()}."
    elif 'wait' in lower or 'pending' in lower:
        return f"Check status with {name} on: {text.lower()}."
    else:
        return f"Follow up with {name} regarding: {text.lower()}."


def get_followups(df):
    blockers_df = get_blockers(df)
    actions = [
        generate_followup_action(row['Name'], row['Blocker'])
        for _, row in blockers_df.iterrows()
    ]
    return pd.DataFrame({'Name': blockers_df['Name'].values, 'Follow-up Action': actions})


# ---------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------

def generate_recommendations(df):
    recommendations = []
    blockers_df = get_blockers(df)

    for _, row in blockers_df.iterrows():
        name = row['Name']
        blocker = row['Blocker'].lower()
        dep_person = extract_dependency_person(row['Blocker'])

        if 'access' in blocker or 'credential' in blocker or 'permission' in blocker:
            recommendations.append(f"Provide/escalate access or credentials for {name}.")
        elif 'approval' in blocker:
            recommendations.append(f"Get approval expedited for {name}'s request.")
        elif dep_person:
            recommendations.append(f"Coordinate between {dep_person} and {name} to resolve dependency.")
        else:
            recommendations.append(f"Check in with {name} to understand and resolve: {row['Blocker']}.")

    for _, row in df.iterrows():
        if row['Yesterday'] and row['Today'] and row['Yesterday'].lower() == row['Today'].lower():
            recommendations.append(
                f"{row['Name']} has been on the same task ('{row['Today']}') for more than a day — check for hidden blockers."
            )

    if not recommendations:
        recommendations.append("No critical action needed today — team is progressing smoothly.")

    return recommendations


# ---------------------------------------------------------------------
# Rule-based summary (fallback, no API key needed)
# ---------------------------------------------------------------------

def generate_rule_based_summary(df):
    total = len(df)
    blockers_df = get_blockers(df)
    pending_df = get_pending_work(df)
    done_count = total - len(pending_df)

    lines = []
    lines.append(
        f"Today, {total} team member(s) submitted updates. "
        f"{done_count} task(s) are fully completed, while {len(pending_df)} are still in progress."
    )

    if len(blockers_df) == 0:
        lines.append("No blockers were reported — the team is moving smoothly with no immediate risks.")
    elif len(blockers_df) == 1:
        name = blockers_df.iloc[0]['Name']
        lines.append(f"One blocker was reported by {name}, which needs attention to avoid delay.")
    else:
        names = ", ".join(blockers_df['Name'].tolist())
        lines.append(
            f"{len(blockers_df)} blockers were reported, affecting {names}. "
            f"These should be prioritized today to prevent the sprint from slipping."
        )

    return " ".join(lines)


# ---------------------------------------------------------------------
# LLM-based summary (OpenAI) — used when an API key is available
# ---------------------------------------------------------------------

def generate_llm_summary(df, api_key=None):
    """
    Uses the OpenAI API to turn the standup data into a polished,
    human-like executive summary. Falls back to the rule-based
    summary if no API key is available.

    Set OPENAI_API_KEY environment variable, or pass api_key directly.
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return generate_rule_based_summary(df) + "\n\n(ℹ️ LLM summary not used — no OPENAI_API_KEY found. Showing rule-based summary instead.)"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        records = df.to_dict(orient='records')
        prompt = (
            "You are an assistant to a Project Lead. Below is today's daily "
            "standup data in JSON format. Write a concise, professional "
            "executive summary (4-6 sentences) covering: overall team "
            "progress, key blockers and who they affect, and what the "
            "Project Lead should prioritize today. Be specific with names.\n\n"
            f"Standup data:\n{records}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful project management assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return generate_rule_based_summary(df) + f"\n\n(⚠️ LLM call failed: {e}. Showing rule-based summary instead.)"


# ---------------------------------------------------------------------
# Combined report dict (handy for HTML/Streamlit/Email use)
# ---------------------------------------------------------------------

def build_report(df, use_llm=False, api_key=None):
    blockers = get_blockers(df)
    pending = get_pending_work(df)
    followups = get_followups(df)
    recommendations = generate_recommendations(df)

    if use_llm:
        summary = generate_llm_summary(df, api_key=api_key)
    else:
        summary = generate_rule_based_summary(df)

    return {
        "summary": summary,
        "blockers": blockers,
        "pending": pending,
        "followups": followups,
        "recommendations": recommendations,
        "total_members": len(df),
        "total_blockers": len(blockers),
        "total_followups": len(followups),
    }
