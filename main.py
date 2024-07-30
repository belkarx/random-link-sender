import streamlit as st
import random
import uuid
import re
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode, parse_qs

# File to store the email database
DB_FILE = "email_database.json"

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_database(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def send_email(recipient, link, orig_sender):
    # Outlook SMTP configuration
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    sender_email = "random-link-sender@outlook.com"
    app_password = os.getenv("OUTLOOK_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = "Your Random Link"

    body = f"Here's a random link {orig_sender} shared: {link}"
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def main():
    st.title("Email Link Sharing App")

    # Load the database
    email_database = load_database()
    print(email_database)

    # Get query parameters
    user_id = st.query_params.get("id", "")

    if user_id and user_id in email_database:
        st.sidebar.success(f"Logged in with ID: {user_id}")
        page = st.sidebar.selectbox("Choose a page", ["Submit Link", "Delete Email"])
    else:
        page = "Submit Email"

    if page == "Submit Email":
        st.header("Submit Your Email")
        email = st.text_input("Enter your email:", key="email_input")
        if st.button("Submit") or (email and st.session_state.get("email_submitted")):
            if is_valid_email(email) and email not in email_database.values():
                user_id = str(uuid.uuid4())
                email_database[user_id] = email
                save_database(email_database)
                new_url = f"{st.get_option('server.baseUrlPath')}?{urlencode({'id': user_id})}"
                st.success(f"Email submitted successfully. Your personal URL is: {new_url}")
                st.markdown(f"Click [here]({new_url}) to access your personalized page.")
                st.session_state.email_submitted = True
            else:
                st.error("Invalid email address. Please try again.")
        st.session_state.email_submitted = False

    elif page == "Submit Link":
        st.header("Submit a Link")
        link = st.text_input("Enter the link you want to share:")
        if st.button("Submit Link"):
            if email_database and len(email_database) > 1:
                random_recipient = random.choice([x for x in list(email_database.values()) if x != email_database[user_id]])
                if send_email(random_recipient, link, email_database[user_id]):
                    st.success(f"Link sent to a random recipient (out of {len(email_database) - 1} available).")
                else:
                    st.error("Failed to send the email. Please try again later.")
            else:
                st.warning("No recipients available. Be the first to submit your email!")

    elif page == "Delete Email":
        st.header("Delete Your Email")
        if st.button("Delete Email"):
            del email_database[user_id]
            save_database(email_database)
            st.success("Your email has been deleted from our records.")
            st.markdown("Click [here](/) to return to the main page.")

if __name__ == "__main__":
    main()
