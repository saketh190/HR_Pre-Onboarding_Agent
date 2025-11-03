# import sqlite3

# # Connect to DB
# conn = sqlite3.connect('candidates.db')
# c = conn.cursor()

# # Fetch all candidates (select all fields)
# c.execute("""
#     SELECT id, name, email, role,
#            offer_sent, accepted,
#            document_link_sent, documents_verified,
#            tickets_generated, policy_welcome_sent
#     FROM candidates
# """)
# rows = c.fetchall()

# for row in rows:
#     print(
#         f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}, "
#         f"Offer Sent: {row[4]}, Accepted: {row[5]}, Document Link Sent: {row[6]}, "
#         f"Documents Verified: {row[7]}, Tickets Generated: {row[8]}, Policy/Welcome Sent: {row[9]}"
#     )

# conn.close()

##the below code is to check if the Gemini API key is loaded correctly and list the available models

from dotenv import load_dotenv
import os
from google import genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Check if key is loaded
print("API Key Loaded:", bool(api_key))  # should print True

client = genai.Client(api_key=api_key)
# List available models to verify access
models = client.models.list()
for model in models:
    print(model.name)

