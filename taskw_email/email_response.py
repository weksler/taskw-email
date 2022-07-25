from .cfg import log
from email.message import EmailMessage
import smtplib
import ssl


class EmailResponse:
    """Sends a response to a previously received task warrior command,
    including the output from task warrior in it.
    """

    def __init__(self, smtp_server, smtp_port, username, password, sender_email, task_line):
        self.smtp_server = smtp_server
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.task_line = task_line
        self.smtp_port = smtp_port
        self.response = ""

    def add_response(self, taskw_response):
        self.response += "\n%s" % taskw_response

    def send_response(self):
        msg = EmailMessage()
        from_email = "Taskwarrior Email Bot <%s>" % self.username
        subject_line = "Re: %s" % self.task_line
        msg['To'] = self.sender_email
        msg['From'] = from_email
        msg['Subject'] = subject_line
        msg.set_content(self.response)
        msg.add_alternative(("""\
        <html>
          <head></head>
          <body>
          <pre>%s
          </pre>
          </body>
        </html>
        """ % self.response), subtype='html')

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
            server.login(self.username, self.password)
            server.sendmail(from_email, self.sender_email, msg.as_string())
            log.debug("Message to %s with subject %s sent successfully", self.sender_email, subject_line)
