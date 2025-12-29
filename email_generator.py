import copy
import os
from pathlib import Path
from typing import List, Dict, Any

import email
from email.message import EmailMessage
from email import policy
from email.parser import BytesParser
import email.utils



class Template:

    def __init__(self, path_to_template: str):
        path = Path(path_to_template)
        with path.open("rb") as fh:
            self.msg: EmailMessage = BytesParser(policy=policy.default).parse(fh)
        if not isinstance(self.msg, EmailMessage):
            raise TypeError("Parsed template is not an EmailMessage; ensure using BytesParser(policy=policy.default)")


def _replace_placeholders_in_text(text: str, replace_dict: Dict[str, Any]) -> str:
    if text is None:
        return text
    result = text
    for key, value in replace_dict.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


class email_draft:
    msg: EmailMessage

    def __init__(self, template: Template, replace_dict: Dict[str, Any]):
        # deep copy so template stays unchanged
        self.msg = copy.deepcopy(template.msg)

        # Replace placeholders only in the Subject header
        if self.msg.get("Subject") is not None:
            original = str(self.msg["Subject"])
            replaced = _replace_placeholders_in_text(original, replace_dict)
            if replaced != original:
            # replace_header updates the existing header instead of adding a duplicate
                self.msg.replace_header("Subject", replaced)

        # If a specific 'Email' field is provided in replace_dict, set To header (fallback handled below)
        if "Email" in replace_dict and not self.msg.get("To"):
            self.msg["To"] = replace_dict.get("Email")

        # Replace placeholders in the body. Handle multipart and singlepart text parts.
        if self.msg.is_multipart():
            for part in self.msg.walk():
                # Only process text parts that are not attachments
                if part.get_content_maintype() == "text" and part.get_content_disposition() != "attachment":
                    payload = part.get_content()
                    new_payload = _replace_placeholders_in_text(payload, replace_dict)
                    if new_payload != payload:
                        # preserve subtype and charset when setting content
                        subtype = part.get_content_subtype()
                        charset = part.get_content_charset()
                        part.set_content(new_payload, subtype=subtype, charset=charset)
        else:
            payload = self.msg.get_content()
            new_payload = _replace_placeholders_in_text(payload, replace_dict)
            if new_payload != payload:
                subtype = self.msg.get_content_subtype()
                charset = self.msg.get_content_charset()
                self.msg.set_content(new_payload, subtype=subtype, charset=charset)

        # Ensure a Message-ID exists
        if not self.msg.get("Message-ID"):
            self.msg["Message-ID"] = email.utils.make_msgid()

        # Ensure To header exists (fallback)
        if not self.msg.get("To"):
            self.msg["To"] = replace_dict.get("email", "NO EMAIL PROVIDED")

    def eml_to_file(self, path_to_file: str):
        out_path = Path(path_to_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as fh:
            fh.write(self.msg.as_bytes(policy=policy.default))


def generate_emails(template_path: str, data: List[Dict[str, Any]], output_folder: str):
    """
    Generate .eml files from a template .eml and a list of dicts.
    Each dict should map placeholder names (without braces) to values.
    Example placeholder in template: {{first_name}}
    """
    tmpl = Template(template_path)
    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, entry in enumerate(data):
        draft = email_draft(tmpl, entry)
        filename = f"email_{i}.eml"
        draft.eml_to_file(str(out_dir / filename))

