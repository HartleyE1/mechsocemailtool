# email_builder.py
# Helper functions and classes for building and managing email data
# This module provides an easy frontend to interact with data structures that represent the components of an email, such as subject, body, sender, and recipient, along with other MIME components. It also includes functions to create and manipulate these email objects, as well as to convert them into formats suitable for sending or displaying.
# This email builder creates, stores and loads HTML templates for emails using the Liquid templating engine. It also provides functions to render these templates with specific data, allowing for dynamic email content generation based on user input or other data sources.

# interactable email data structure

import email
import os
import re
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
        body = _normalize_liquid(body)
        subject = _normalize_liquid(subject)
        self.dynamic_body = parse(body)
        self.dynamic_subject = parse(subject)
    
    def render_content(self, data):
        body = self.dynamic_body.render(data)
        subject = self.dynamic_subject.render(data)
        return body, subject

    def set_data(self, data: dict):
        self.data = data

    def get_data(self):
        return self.data

    def build_email(self):
        
        #render the email data into a MIME email object that can be sent using an email sending service

        body, subject = self.render_content(self.data)

        msg = email.message.EmailMessage()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = subject
        msg.set_content(body, subtype='html')

        msg['X-Unsent'] = '1'

        msg['Message-ID'] = email.utils.make_msgid()


        return msg
    



class EmailBuffer:
    def __init__(self):
        self.emails = []
        self.template = None
        self.data =[{}]
    
    def compile_emails(self):
        self.emails = []
        for record in self.data:
            email_addr = _get_value_by_key_regex(record, r"^(email|recipient)$")
            if email_addr and not verify_email_address(email_addr):
                email_addr = ""

            email_obj = Email(
                subject=self.template.subject,
                body=self.template.body,
                sender=self.template.sender,
                recipient=self.template.recipient,
            )
            if email_addr:
                email_obj.recipient = email_addr
            email_obj.parse_template(self.template.body, self.template.subject)
            email_obj.set_data(record)
            self.emails.append(email_obj)
        
    def get_emails(self):
        return self.emails
    
    def set_template(self, template):
        self.template = template

    def set_data(self, data):
        self.data = data
    
    def set_data_from_pandas(self, df):
        self.data = df.to_dict(orient='records')

    def export_emails(self, path: str = "./emails"):
        if os.path.isabs(path):
            path = os.path.normpath(path)

        if not os.path.exists(path):
            os.makedirs(path)
        for i, email in enumerate(self.emails):
            email_msg = email.build_email()
            with open(os.path.join(path, f"email_{i+1}.eml"), "wb") as f:
                f.write(email_msg.as_bytes())


def _normalize_liquid(text: str) -> str:
    if not text:
        return text
    # Fix missing closing brace for simple {{ var }} tags.
    return re.sub(r"{{([^{}]*?)}(?!})", r"{{\1}}", text)


def _get_value_by_key_regex(data: dict, pattern: str):
    regex = re.compile(pattern, re.IGNORECASE)
    for key, value in data.items():
        if regex.search(str(key)):
            return value
    return None
    





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

    def get_frontmatter(self):
        #returns the frontmatter of the template as yaml data
        yaml_data = {
            "subject": self.subject,
            "sender": self.sender,
            "recipient": self.recipient
        }
        return yaml.dump(yaml_data)

    def set_frontmatter(self, yaml_string: str):
        #implement later. sets frontmatter of the template for advanced editing of the template in the gui.
        pass



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


