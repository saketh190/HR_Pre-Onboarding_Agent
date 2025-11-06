import streamlit as st
import yagmail
from dotenv import load_dotenv
import os
from check_responses import init_db, add_candidate, get_all_candidates
import subprocess
import signal

# ✅ Function to start agent.py only once
def start_agent():
    if "agent_running" not in st.session_state:
        st.session_state.agent_running = False

    if not st.session_state.agent_running:
        try:
            # Run agent.py in background
            subprocess.Popen(["python", "agent.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            st.session_state.agent_running = True
            st.sidebar.success("✅ Agent is running in background.")
        except Exception as e:
            st.sidebar.error(f"⚠ Failed to start agent.py: {e}")

# ✅ Start agent when dashboard opens
start_agent()

# ---------- LOAD ENV ----------
load_dotenv()
EMAIL_ADDRESS = st.secrets("EMAIL_ADDRESS")
EMAIL_PASSWORD = st.secrets("EMAIL_PASSWORD")

# ---------- INIT DB ----------
init_db()

# ---------- EMAIL SETUP ----------
yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)

# ---------- STREAMLIT UI ----------
st.title("HR Onboarding Agent Dashboard")

# --- Add Candidate ---
st.subheader("Add New Candidate")
name = st.text_input("Candidate Name")
email = st.text_input("Candidate Email")
role = st.text_input("Role")

if st.button("Start Onboarding"):
    if name and email and role:
        # Send Offer Email first
        subject = "Welcome to the Company!"
        content = f"""Hello {name},

We are happy to have you as our {role}.
Please reply 'Yes' to accept this offer.

Regards,
HR Team
"""
        try:
            yag.send(email, subject, content)

            # ✅ Only add to DB if email sent successfully
            add_candidate(name, email, role)

            # ✅ Mark offer_sent = 'Yes'
            import sqlite3
            conn = sqlite3.connect("candidates.db")
            c = conn.cursor()
            c.execute("UPDATE candidates SET offer_sent='Yes' WHERE email=?", (email,))
            conn.commit()
            conn.close()

            st.success(f"Offer sent to {name} ({role}) successfully!")

        except Exception as e:
            st.error(f"Failed to send email. Candidate not added to database. Error: {e}")
    else:
        st.error("Please fill all fields")

# --- Show Candidate Status ---
st.subheader("Candidate Onboarding Status")

# Toggle button to switch views
view_mode = st.radio("Choose View:", ["Timeline View", "Table View"])

# Function for timeline-style dots
def progress_step(is_done):
    if is_done == "Yes":
        return "<span style='color:#00C853;font-size:22px;font-weight:bold;'>●</span>"
    else:
        return "<span style='color:#D50000;font-size:22px;font-weight:bold;'>○</span>"

candidates = get_all_candidates()

if not candidates:
    st.info("No candidates available.")
else:
    for cand in candidates:
        name, email, role = cand[1], cand[2], cand[3]

        if view_mode == "Timeline View":
            # Header
            st.markdown(f"### 👤 {name} — *{role}*")
            st.markdown(f"📧 {email}")

            # Steps: Offer, Accept, Doc Link, Verify Docs, Tickets, Welcome Mail
            steps = [
                progress_step(cand[4]),
                progress_step(cand[5]),
                progress_step(cand[6]),
                progress_step(cand[7]),
                progress_step(cand[8]),
                progress_step(cand[9])
            ]

            # Connect with lines
            timeline = "──".join(steps)

            # Display dots
            st.markdown(f"<div style='font-size:20px; font-weight:bold;'>{timeline}</div>", unsafe_allow_html=True)

            # Labels below
            st.markdown("""
            <div style='font-size:14px; color:gray;'>
            Offer&nbsp;&nbsp;&nbsp;&nbsp;Accept&nbsp;&nbsp;&nbsp;&nbsp;Docs&nbsp;&nbsp;&nbsp;&nbsp;Verify&nbsp;&nbsp;&nbsp;&nbsp;Ticket&nbsp;&nbsp;&nbsp;&nbsp;Welcome
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

        elif view_mode == "Table View":
            import pandas as pd

            # ✅ Create one table for all candidates (not inside the loop)
            df = pd.DataFrame(candidates, columns=[
                "ID", "Name", "Email", "Role", "Offer Sent",
                "Accepted", "Docs Link Sent", "Docs Verified",
                "Tickets Done", "Welcome Mail"
            ])

            # ✅ Show a clean scrollable table
            st.dataframe(
                df.style.set_properties(**{
                    'white-space': 'nowrap',   # Prevent text wrap
                    'text-align': 'center'
                }),
                use_container_width=True,
                height=300
            )
            # ✅ Stop further looping after table is displayed
            st.stop()

