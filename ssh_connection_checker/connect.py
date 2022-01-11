import os
import re
import time
import socket
import smtplib
import logging
from ast import literal_eval
from dotenv import load_dotenv
from email.message import EmailMessage
from ssh2.session import Session

"""
This script is for two things:
1. Check if a SSH connection is stable.
2. Check the storage status in the remote machine.
"""

logging.basicConfig(
    format="{asctime} {message}",
    filename="ssh_error.log",
    level=logging.INFO,
    encoding="utf-8",
    filemode="a",
    style="{",
)
# Load env variables
load_dotenv()
# Define local variables for the run
host = os.environ.get("SSH_HOST")
user = os.environ.get("SSH_USERNAME")
password = os.environ.get("SSH_PASSWORD")
port = int(os.environ.get("PORT"))

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_MAIL = os.environ.get("TO_MAIL")

connected = False


def send_mail(subject, body):
    """
    This function performs an email sending to the TO_MAIL address defined above
    """
    to_mail = literal_eval(TO_MAIL)
    for mail in to_mail:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = mail
        msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        logging.info("Mail sent to {mail}")


def check_conection(session):
    """
    This function checks the connection to the SSH_HOST address defined above. 
    If there is not a connection, an email will be send to TO_MAIL addresses.
    It also checks the disk capacity. If the capacity is above 80%. an email will be send to TO_MAIL addresses.
    """
    channel = session.open_session()
    channel.shell()
    channel.write("echo hello\n")
    channel.write("df -h /\n")
    time.sleep(1)
    size, data = channel.read()
    result = data.decode()
    pattern = re.compile(r"\s{2}(?P<num>\d{1,3})\%\s\/")
    match = pattern.search(result)
    used_space = int(match.group("num"))
    if used_space > 80:
        subject = "Storage is above 80%"
        body = f"Current disk usage is {used_space}% full"
        send_mail(subject, body)
    logging.info("Connection sucessful, exiting connection now")
    channel.close()
    logging.info(f"Exit status {channel.get_exit_status()}")


def main():
    """
    Main function of the script.
    """
    # Try to connect to host IP
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        session = Session()
        session.handshake(sock)
        session.userauth_password(user, password)
        connected = True

    except Exception as E:
        connected = False
    # If succeeded, check the connection and the disk usage
    if connected:
        check_conection(session)
    else:
        subject = "SSH Not Running"
        body = "Hi this is a email to notify that the ssh connection is failed."
        send_mail(subject, body)


if __name__ == "__main__":
    main()
