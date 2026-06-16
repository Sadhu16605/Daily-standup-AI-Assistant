"""
streamlit_app.py
-------------------
Daily Standup AI Assistant — Streamlit Dashboard

Run with:
    streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import standup_core as core
from email_notifier import send_standup_email
import os

st.set_page_config(
    page_title="Daily Standup AI Assistant",
    page_icon="📋",
    layout="wide",
)

# ---------------------------------------------------------------------
# Minimal custom styling
# ---------------------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .metric-card {
        background-color: #f0f4ff;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    h1, h2, h3 { color: #1a1a2e; }
</style>
""", unsafe_allow_html=True)

st.title("📋 Daily Standup AI Assistant")
st.caption("Upload your team's standup CSV to get blockers, follow-ups, and AI-powered recommendations instantly.")

# ---------------------------------------------------------------------
# Sidebar — settings
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    use_llm = st.toggle("Use AI (OpenAI) summary", value=False,
                         help="Requires an OpenAI API key. If off, a rule-based summary is used instead.")

    api_key_input = ""
    if use_llm:
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=os.environ.get("OPENAI_API_KEY", ""),
            type="password",
            help="Your key is used only for this session and is not stored."
        )

    st.divider()
    st.subheader("📧 Email Notification")
    enable_email = st.toggle("Send summary via email", value=False)

    sender_email = receiver_email = sender_password = ""
    if enable_email:
        sender_email = st.text_input("Sender Gmail address", value=os.environ.get("STANDUP_EMAIL_SENDER", ""))
        sender_password = st.text_input("Sender App Password", type="password",
                                         help="Use a Gmail App Password, not your normal password.")
        receiver_email = st.text_input("Recipient email (Project Lead)",
                                        value=os.environ.get("STANDUP_EMAIL_RECEIVER", ""))

# ---------------------------------------------------------------------
# Main — file upload
# ---------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload standup CSV", type=["csv"])

use_sample = False
if uploaded_file is None:
    use_sample = st.checkbox("Use sample data instead", value=True)

df = None
if uploaded_file is not None:
    df = core.load_standup_data(uploaded_file)
elif use_sample and os.path.exists("standup.csv"):
    df = core.load_standup_data("standup.csv")

if df is None:
    st.info("Upload a CSV file with columns: Name, Yesterday, Today, Blocker, Status")
    st.stop()

with st.expander("📄 Raw standup data"):
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------
with st.spinner("Analyzing standup data..."):
    report = core.build_report(df, use_llm=use_llm, api_key=api_key_input or None)

# ---------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("👥 Team Members", report["total_members"])
col2.metric("🚧 Blockers", report["total_blockers"])
col3.metric("📞 Follow-ups", report["total_followups"])

st.divider()

# ---------------------------------------------------------------------
# AI Overview
# ---------------------------------------------------------------------
st.subheader("🧠 Overview")
st.write(report["summary"])

st.divider()

# ---------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🚧 Blockers", "⏳ Pending Work", "📞 Follow-up Actions", "✅ Recommendations"])

with tab1:
    if report["blockers"].empty:
        st.success("No blockers today! 🎉")
    else:
        st.dataframe(report["blockers"], use_container_width=True, hide_index=True)

with tab2:
    if report["pending"].empty:
        st.success("No pending work.")
    else:
        st.dataframe(report["pending"], use_container_width=True, hide_index=True)

with tab3:
    if report["followups"].empty:
        st.success("No follow-ups needed.")
    else:
        st.dataframe(report["followups"], use_container_width=True, hide_index=True)

with tab4:
    for i, rec in enumerate(report["recommendations"], 1):
        st.markdown(f"**{i}.** {rec}")

st.divider()

# ---------------------------------------------------------------------
# Email send button
# ---------------------------------------------------------------------
if enable_email:
    if st.button("📧 Send Summary Email", type="primary"):
        if not all([sender_email, sender_password, receiver_email]):
            st.error("Please fill in all email fields in the sidebar.")
        else:
            try:
                send_standup_email(
                    report,
                    sender_email=sender_email,
                    sender_password=sender_password,
                    receiver_email=receiver_email,
                )
                st.success(f"Email sent to {receiver_email}! ✅")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
else:
    st.caption("Enable 'Send summary via email' in the sidebar to email this report to the Project Lead.")
