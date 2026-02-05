"""Test Azure Communication Services Email"""

from azure.communication.email import EmailClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection string from .env
conn_str = os.getenv("AZURE_COMM_CONNECTION_STRING")
from_email = os.getenv("FROM_EMAIL")

client = EmailClient.from_connection_string(conn_str)

message = {
    "senderAddress": from_email,
    "recipients": {
        "to": [{"address": "curtis.prince@xigusa.com"}]
    },
    "content": {
        "subject": "Eagle Harbor Monitor - Email Test",
        "html": "<h1>✅ Success!</h1><p>Azure Communication Services is configured and working correctly.</p><p>Your Eagle Harbor Monitor email system is ready!</p>"
    }
}

print("Sending test email to curtis.prince@xigusa.com...")
poller = client.begin_send(message)
result = poller.result()
print(f"✅ Email sent successfully!")
print(f"Message ID: {result['id']}")
print(f"Status: {result['status']}")
print("\nCheck your inbox at curtis.prince@xigusa.com")
