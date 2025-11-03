import streamlit as st
import yagmail
from dotenv import load_dotenv
import os
from check_responses import init_db, add_candidate, get_all_candidates

# ---------- LOAD ENV ----------
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

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
st.subheader("All Candidates Status")
candidates = get_all_candidates()
if candidates:
    for cand in candidates:
        st.write({
            "Name": cand[1],
            "Email": cand[2],
            "Role": cand[3],
            "Offer Sent": cand[4],
            "Accepted": cand[5],
            "Document Link Sent": cand[6],
            "Documents Verified": cand[7],
            "Tickets Generated": cand[8],
            "Policy & Welcome Sent": cand[9]
        })
else:
    st.info("No candidates added yet.")
