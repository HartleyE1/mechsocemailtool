import re
import webview
import os
import re

from temp_email import TEMP_EML_PATH

import email
from email.message import EmailMessage
from email import policy
from email.parser import BytesParser
import email.utils

def load_template_from_path(template_path):
    with open(template_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    if not isinstance(msg, EmailMessage):
        raise TypeError("Parsed template is not an EmailMessage; ensure using BytesParser(policy=policy.default)")
    with open(TEMP_EML_PATH, 'wb') as f:
        f.write(msg.as_bytes())

def create_new_email_template():
    # Create a basic email template
    msg = EmailMessage()
    with open(TEMP_EML_PATH, 'wb') as f:
        f.write(msg.as_bytes())

def update_temp_email(html_content, text_content, subject=None):
    # Load the existing temp email
    with open(TEMP_EML_PATH, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    if not isinstance(msg, EmailMessage):
        raise TypeError("Parsed template is not an EmailMessage")

    # Remove all existing body parts (important!)
    msg.clear_content()

    # Rebuild the body as multipart/alternative
    msg.set_content(text_content)                     # text/plain
    msg.add_alternative(html_content, subtype='html') # text/html

    # Update subject if provided
    if subject and subject.strip():
        msg['Subject'] = subject

    # Save back to the temp email file
    with open(TEMP_EML_PATH, 'wb') as f:
        f.write(msg.as_bytes())


def get_body_from_email():
    with open(TEMP_EML_PATH, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    # Try HTML first
    html_part = msg.get_body(preferencelist=('html'))
    if html_part:
        return html_part.get_content()

    # Fallback to plain text
    plain_part = msg.get_body(preferencelist=('plain'))
    if plain_part:
        return plain_part.get_content()

    # Fallback 3
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ('text/html', 'text/plain'):
                return part.get_content()

    # AHHHHHHHHH just return empty idc
    return ""

def get_subject_from_email():
    with open(TEMP_EML_PATH, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg.get('Subject', '')



class API:
    def save_html(self, html, text, subject=None):
        print("Received HTML:")
        print(html)
        print("Received Text:")
        print(text)
        update_temp_email(html, text, subject)
    
    def open_file(self):
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=('Email files (*.eml)', 'All files (*.*)')
        )

        if result:
            template_path = result[0]
            load_template_from_path(template_path)
        
        html_content = get_body_from_email()

        return html_content
    
    def save_email_template(self, html, text, subject=None):

        update_temp_email(html, text, subject)

        window = webview.active_window()
        if not window:
            print("No active window :(")
            return
        
        result = window.create_file_dialog(
            webview.FileDialog.SAVE,
            allow_multiple=False,
            file_types=('Email files (*.eml)', 'All files (*.*)')
        )

        if result:
            path = result[0]
            with open(TEMP_EML_PATH, 'rb') as f_src:
                with open(path, 'wb') as f_dst:
                    f_dst.write(f_src.read())


api = API()



def open_editor(existing_html=None, existing_subject=None):

    if TEMP_EML_PATH is None or not os.path.exists(TEMP_EML_PATH):
        create_new_email_template()
    else:
        existing_html = get_body_from_email()
        existing_subject = get_subject_from_email()

    updated_html = html.replace("{{BODY}}", existing_html or "")
    updated_html = updated_html.replace("{{SUBJECT}}", existing_subject or "")

    webview.create_window("Email Editor", html=updated_html, width=800, height=600, js_api=api)
    webview.start()


###--Webview HTML Content--###

html = """
<!DOCTYPE html>
<html>
  <head>
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
  </head>
  <body>
    <h1>Email Template Editor</h1>

    <script>
      function openFile() {
        window.pywebview.api.open_file().then(html_content => {
          const delta = quill.clipboard.convert(html_content);
          quill.setContents(delta);
        });
      }

        function saveTemplate() {
            const html = quill.root.innerHTML;
            const text = quill.getText();
            const subject = document.getElementById("subject").value;
            window.pywebview.api.save_email_template(html, text, subject);
        }
    </script>

    <ul style="list-style-type: none; padding: 0;">
    <li style="float: left; padding-right: 10px;"><button onclick="openFile()" style="margin-bottom: 10px;">Open Template File</button></li>
    <li style="float: left; padding-right: 10px;"><button onclick="saveTemplate()" style="margin-bottom: 10px;">Save Email Template</button></li>
    </ul>

    <input type="text" id="subject" placeholder="Subject" style="width: 100%; padding: 10px; margin-bottom: 10px; font-size: 16px;">
    <div id="editor" style="height: 300px; margin-bottom: 10px;"></div>
    <button onclick="sendToPython()">Save</button>

    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
      var ColorStyle = Quill.import('attributors/style/color');
      var BackgroundStyle = Quill.import('attributors/style/background');
      Quill.register(ColorStyle, true);
      Quill.register(BackgroundStyle, true);

      var quill = new Quill('#editor', {
        theme: 'snow',
        modules: {
          toolbar: [
            [{ 'color': ['#000000', '#FFFFFF', '#ed1335', '#161616'] }],
            ['bold', 'italic', 'underline'],
            ['clean']
          ]
        }
      });

      function sendToPython() {
        const html = quill.root.innerHTML;
        const text = quill.getText();
        const subject = document.getElementById("subject").value;
        window.pywebview.api.save_html(html, text, subject);
      }
    </script>
    <script>
        const existingHTML = `{{BODY}}`;
        const existingSubject = `{{SUBJECT}}`;

        document.getElementById("subject").value = existingSubject;

        window.addEventListener('pywebviewready', () => {
            const delta = quill.clipboard.convert(existingHTML);
            quill.setContents(delta);
        });
    </script>
  </body>
</html>
"""

###--End of Webview HTML Content--###

def launch_editor_process():
    from email_builder import open_editor
    open_editor()

if __name__ == "__main__":
    open_editor()