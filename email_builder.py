# email_builder.py
# Helper functions and classes for building and managing email data
# This module provides an easy frontend to interact with data structures that represent the components of an email, such as subject, body, sender, and recipient, along with other MIME components. It also includes functions to create and manipulate these email objects, as well as to convert them into formats suitable for sending or displaying.
# This email builder creates, stores and loads HTML templates for emails using the Liquid templating engine. It also provides functions to render these templates with specific data, allowing for dynamic email content generation based on user input or other data sources.

# interactable email data structure

import email
import os
from liquid import parse, render
import yaml

class Email:

    def __init__(self, subject: str, body: str, sender: str = "", recipient: str = ""):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.recipient = recipient
        self.data = {}


    def __str__(self):
        return f"From: {self.sender}\nTo: {self.recipient}\nSubject: {self.subject}\n\n{self.body}"
    
    def parse_template(self, body, subject):
        self.dynamic_body = parse(body)
        self.dynamic_subject = parse(subject)
    
    def render_content(self, data):
        body = self.dynamic_body.render(data)
        subject = self.dynamic_subject.render(data)
        return body, subject

    def data(self, data: dict = {}):
        if data:
            self.data = data
        else:
            return self.data

    def build_email(self):
        
        #render the email data into a MIME email object that can be sent using an email sending service

        body, subject = self.render_content(self.data)

        msg = email.message.EmailMessage()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = subject
        msg.set_content(body, subtype='html')
        return msg
    





class template:
    def __init__(self, subject: str, body: str, sender: str = "", recipient: str = ""):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.recipient = recipient

    #function to export the template as a file type which this program can read and use to create an email object
    def export(self, filename: str, path: str = "./"):
        if os.path.isabs(filename):
            file_path = os.path.normpath(filename)
        else:
            base_path = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
            file_path = os.path.normpath(os.path.join(base_path, filename))
        with open(file_path, "w") as file:
            file.write(f"---\n")
            yaml_data = {
                "subject": self.subject,
                "sender": self.sender,
                "recipient": self.recipient
            }
            file.write(yaml.dump(yaml_data))
            file.write(f"---\n")
            file.write(f"{self.body}\n")
            


#function to load a template from a file and return a template object
def load(filename: str, path: str = "./"):
    file_path = filename if os.path.isabs(filename) else os.path.join(path, filename)
    with open(file_path, "r") as file:
        content = file.read()

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Template is missing YAML frontmatter.")

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break

    if end_index is None:
        raise ValueError("Template frontmatter is not closed with '---'.")

    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1:])

    data = yaml.safe_load(frontmatter) or {}
    subject = data.get("subject", "")
    sender = data.get("sender", "")
    recipient = data.get("recipient", "")

    return template(subject=subject, body=body, sender=sender, recipient=recipient)

def loads(template_string: str):
    lines = template_string.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Template is missing YAML frontmatter.")

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break

    if end_index is None:
        raise ValueError("Template frontmatter is not closed with '---'.")

    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1:])

    data = yaml.safe_load(frontmatter) or {}
    subject = data.get("subject", "")
    sender = data.get("sender", "")
    recipient = data.get("recipient", "")

    return template(subject=subject, body=body, sender=sender, recipient=recipient)


def verify_email_address(email_address: str) -> bool:
    # simple regex to check if the email address is valid
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email_address) is not None