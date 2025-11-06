import imapclient
import pyzmail
import sqlite3
import yagmail
import json
from dotenv import load_dotenv
import os
import time
from e_table import get_all_employees, add_employee
from check_responses import init_db, add_candidate, get_all_candidates
import sqlite3
# ---------- LOAD ENV ----------
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- EMAIL SETUP ----------
yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)

# ---------- LLM SETUP (Google Gemini using google-genai) ----------
# ---------- FILES ----------
TICKET_FILE = "tickets.json"
FORM_LINK = "https://forms.office.com/r/j3sUEjNxvS"  # Replace with your form
 # Replace with your form

# ---------- FUNCTIONS ----------


import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def is_acceptance_email(body):
    prompt = f"""
    You are an AI assistant for HR onboarding.

    This is the candidate's reply:
    "{body}"

    Decide if the candidate is ACCEPTING or REJECTING the job offer.
    Reply only with:
    accept
    reject
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return "accept" in response.text.strip().lower()




def check_candidate_replies():
    """Check Gmail for any candidate reply and decide via AI if it is acceptance."""
    imap_server = 'imap.gmail.com'
    mail = imapclient.IMAPClient(imap_server, ssl=True)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select_folder('INBOX')

    uids = mail.search(['UNSEEN'])
    accepted_emails = []

    for uid in uids:
        raw_message = mail.fetch([uid], ['BODY[]', 'FLAGS'])
        message = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])
        sender = message.get_addresses('from')[0][1]

        if message.text_part:
            body = message.text_part.get_payload().decode(message.text_part.charset)
        elif message.html_part:
            body = message.html_part.get_payload().decode(message.html_part.charset)
        else:
            body = ""

        # ✅ Use AI to detect if this message is an acceptance
        if is_acceptance_email(body):
            accepted_emails.append(sender)

    mail.logout()
    return accepted_emails

def update_status(email, column, value="Yes"):
    """Update specific column in DB"""
    conn = sqlite3.connect('candidates.db')
    c = conn.cursor()
    c.execute(f"UPDATE candidates SET {column}=? WHERE email=?", (value, email))
    conn.commit()
    conn.close()

def send_offer_email(name, email, role):
    subject = "Welcome to the Company!"
    content = f"""Hello {name},

We are happy to have you as our {role}.
Please reply 'Yes' to accept this offer.

Regards,
HR Team
"""
    yag.send(email, subject, content)
    update_status(email, "offer_sent")
    print(f"Offer sent to {name} ({email})")

def send_document_link(name, email):
    subject = "Submit Your Documents"
    content = f"""Hello {name},

Congratulations! Please submit your documents here: {FORM_LINK}

Regards,
HR Team
"""
    yag.send(email, subject, content)
    update_status(email, "document_link_sent")
    print(f"Document link sent to {name} ({email})")

def create_tickets(candidate_email, candidate_name, role):
    # Load existing tickets
    try:
        with open(TICKET_FILE, "r") as f:
            tickets = json.load(f)
    except FileNotFoundError:
        tickets = []

    # Account ticket
    account_ticket = {
        "type": "Account Setup",
        "candidate_name": candidate_name,
        "email": candidate_email,
        "role": role,
        "status": "Pending"
    }

    # Hardware ticket
    hardware_ticket = {
        "type": "Hardware Setup",
        "candidate_name": candidate_name,
        "email": candidate_email,
        "role": role,
        "status": "Pending"
    }

    tickets.append(account_ticket)
    tickets.append(hardware_ticket)

    with open(TICKET_FILE, "w") as f:
        json.dump(tickets, f, indent=4)

    update_status(candidate_email, "tickets_generated")
    print(f"Tickets generated for {candidate_name} ({candidate_email})")

def generate_welcome_email(name, role):
    prompt = f"""
    Write a short welcome email for a new employee:
    - Name: {name}
    - Role: {role}
    - Tone: simple, friendly, professional
    - Under 120 words.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()




    # Extract text from response. The exact path may vary by library version; try common options:
    text = None
    # Option 1: top-level 'content' or 'candidates'
    if hasattr(response, "content") and isinstance(response.content, str):
        text = response.content
    elif isinstance(response, dict):
        # new client often returns dict with 'candidates' -> list -> {'content': '...'}
        if "candidates" in response and len(response["candidates"]) > 0:
            cand = response["candidates"][0]
            if isinstance(cand, dict) and "content" in cand:
                # some responses have nested structure
                if isinstance(cand["content"], str):
                    text = cand["content"]
                elif isinstance(cand["content"], dict) and "text" in cand["content"]:
                    text = cand["content"]["text"]
        # fallback: check for 'output' or 'message'
        if text is None:
            if "output" in response and isinstance(response["output"], str):
                text = response["output"]
            elif "message" in response and isinstance(response["message"], dict):
                # try to find text in message
                for k in ("content", "text"):
                    if k in response["message"] and isinstance(response["message"][k], str):
                        text = response["message"][k]
                        break

    # Final fallback: convert response to string
    if text is None:
        text = str(response)

    return text

def send_policy_welcome(name, email, role):
    content = generate_welcome_email(name, role)
    yag.send(email, "Welcome to the Company!", content)
    update_status(email, "policy_welcome_sent")

    # ✅ Update employee table (mark Joined = Yes)
    conn = sqlite3.connect('employees.db')
    c = conn.cursor()
    c.execute("UPDATE employees SET joined='Yes' WHERE email=?", (email,))
    conn.commit()
    conn.close()

    print(f"🎉 {name} has completed onboarding.")

def auto_add_new_employees():
    employees = get_all_employees()
    for emp in employees:
        if emp['joined'] == 'No':  # New employee
            name = emp['name']
            email = emp['email']
            role = emp['role']

            # Add to candidates table (same as manual add)
            add_candidate(name, email, role)

            # Send offer email
            send_offer_email(name, email, role)

            # Update employee table to avoid repeat
            conn = sqlite3.connect('employees.db')
            c = conn.cursor()
            c.execute("UPDATE employees SET joined = 'In Progress' WHERE email=?", (email,))
            conn.commit()
            conn.close()

            print(f"✅ Auto-started onboarding for {name} ({email})")

# ---------- MAIN AGENT LOOP ----------
def run_agent():
    while True:
        auto_add_new_employees()

        # ✅ AI-based acceptance detection
        accepted_emails = check_candidate_replies()
        for email in accepted_emails:
            update_status(email, "accepted")

        conn = sqlite3.connect('candidates.db')
        c = conn.cursor()

        # 2. Send document link
        c.execute("SELECT name, email FROM candidates WHERE accepted='Yes' AND document_link_sent='No'")
        for name, email in c.fetchall():
            send_document_link(name, email)

        # 3. Create tickets
        c.execute("SELECT name, email, role FROM candidates WHERE documents_verified='Yes' AND tickets_generated='No'")
        for name, email, role in c.fetchall():
            create_tickets(email, name, role)

        # 4. Send welcome mail
        c.execute("SELECT name, email, role FROM candidates WHERE tickets_generated='Yes' AND policy_welcome_sent='No'")
        for name, email, role in c.fetchall():
            send_policy_welcome(name, email, role)

        time.sleep(10)

if __name__ == "__main__":
    run_agent()
