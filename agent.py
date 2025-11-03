import imapclient
import pyzmail
import sqlite3
import yagmail
import json
from dotenv import load_dotenv
import os
import time

# ---------- LOAD ENV ----------
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- EMAIL SETUP ----------
yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)

# ---------- LLM SETUP (Google Gemini using google-genai) ----------
# Install first: pip install google-genai
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------- FILES ----------
TICKET_FILE = "tickets.json"
FORM_LINK = "https://forms.office.com/r/j3sUEjNxvS"  # Replace with your form
 # Replace with your form

# ---------- FUNCTIONS ----------
def check_candidate_replies():
    """Check Gmail for candidate replies with 'Yes'"""
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
        body = ""
        if message.text_part:
            body = message.text_part.get_payload().decode(message.text_part.charset)
        elif message.html_part:
            body = message.html_part.get_payload().decode(message.html_part.charset)

        if "yes" in body.lower():
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
    Write a short and simple welcome email for a new employee.
    Details:
    - Name: {name}
    - Role: {role}
    - Tone: friendly, professional, simple
    - No fancy words, no special characters, no long paragraphs.
    - Mention that HR will share company policies and onboarding details soon.
    - Maximum 120 words.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    try:
        return response.text.strip()
    except:
        return str(response)



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
    print(f"Policy & Welcome email sent to {name} ({email})")

# ---------- MAIN AGENT LOOP ----------
def run_agent():
    while True:
        # 1. Check candidate replies
        accepted_emails = check_candidate_replies()
        for email in accepted_emails:
            update_status(email, "accepted")
            print(f"Candidate {email} accepted the offer.")

        conn = sqlite3.connect('candidates.db')
        c = conn.cursor()

        # 2. Send document links to accepted candidates not yet sent
        c.execute("SELECT name, email FROM candidates WHERE accepted='Yes' AND document_link_sent='No'")
        rows = c.fetchall()
        for row in rows:
            name, email = row
            send_document_link(name, email)

        # 3. Generate tickets for verified documents
        c.execute("SELECT name, email, role FROM candidates WHERE documents_verified='Yes' AND tickets_generated='No'")
        rows = c.fetchall()
        for row in rows:
            name, email, role = row
            create_tickets(email, name, role)

        # 4. Send policy + welcome email for candidates with tickets generated
        c.execute("SELECT name, email, role FROM candidates WHERE tickets_generated='Yes' AND policy_welcome_sent='No'")
        rows = c.fetchall()
        for row in rows:
            name, email, role = row
            send_policy_welcome(name, email, role)

        conn.close()
        # Sleep for 60 seconds
        time.sleep(10)

if __name__ == "__main__":
    run_agent()
