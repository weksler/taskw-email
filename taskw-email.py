import re

from decouple import config
import email
from email.message import EmailMessage
import imaplib
import logging
from subprocess import run
import smtplib
import ssl
import sys


class TaskEmails:
    def __init__(self, imap_server, imap_user, imap_password, sender_email):
        self.imap_server = imap_server
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.sender_email = sender_email
        self.conn = imaplib.IMAP4_SSL(imap_server)
        try:
            self.conn.login(imap_user, imap_password)
        except Exception as e:
            log.critical("failed to connect to server %s as user %s (exception %s)", imap_server, imap_user, e,
                         exc_info=True)
            raise RuntimeError

    def __del__(self):
        try:
            self.conn.close()
        except:
            None  # ignore

    def __iter__(self):
        retcode, messages = self.conn.select("INBOX")
        if retcode != 'OK':
            raise RuntimeError("Got error <" + retcode + "> when selecting INBOX")
        log.debug("INBOX contains %s messages", int(messages[0]))
        return self

    def __next__(self):
        retcode, messages = self.conn.search(None, '(UNSEEN)')
        if retcode != 'OK':
            log.critical("Error fetching unread messages - return code %s", retcode)
            raise StopIteration

        unread_messages = messages[0].decode('utf-8').strip().split()
        if len(unread_messages) == 0:
            log.debug("No unread messages.")
            raise StopIteration

        for unread_message_num in unread_messages:
            log.debug("Now processing message %s", unread_message_num)
            retcode, data = self.conn.fetch(unread_message_num, '(RFC822)')
            if retcode != 'OK':
                log.critical("Error fetching message %s, return code %s", unread_message_num, retcode)
                raise StopIteration
            msg = email.message_from_bytes(data[0][1])
            sender = msg['From']
            subject = msg['Subject']
            log.debug("Message from %s with subject %s", sender, subject)
            if self.sender_email not in sender:
                log.critical("Will not process tasks from %s", sender)
                continue

            return subject


class TaskWarriorCmdLine:
    def __init__(self):
        result = run("which task", shell=True, capture_output=True)
        if result.returncode != 0:
            log.critical("Failed to find taskw executable.")
            raise RuntimeError
        self.taskw = result.stdout.strip().decode()
        log.debug("Task warrior executable is %s", self.taskw)

    def __del__(self):
        cmdline = [self.taskw, 'sync']
        result = run(cmdline, shell=False, capture_output=True)
        log.debug("task sync returned %s - %s%s", result.returncode, result.stdout.decode(), result.stderr.decode())

    def process_line(self, task_line):
        task_line = task_line.strip()
        if TASKCMD_RE_MATCHER.match(task_line):
            return "taskcmd not yet implemented (%s)" % task_line
        elif TASK_RE_MATCHER.match(task_line):
            return self.add_task(task_line[len(TASK_KEYWORD):])
        else:
            return "Couldn't figure out what to do with %s" % task_line

    def add_task(self, task_line):
        cmdline = [self.taskw, 'add'] + task_line.split()
        result = run(cmdline, shell=False, capture_output=True)
        response = "%s%s (%s)" % (result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode)
        log.debug("task add %s - response is %s", task_line, response)
        return response


class EmailResponse:
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
        msg.set_content(self.response)
        from_email = "Taskwarrior Email Bot <%s>" % self.username
        subject_line = "Re: %s" % self.task_line
        msg['To'] = self.sender_email
        msg['From'] = from_email
        msg['Subject'] = subject_line
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
            server.login(self.username, self.password)
            server.sendmail(from_email, self.sender_email, msg.as_string())
            log.debug("Message to %s with subject %s sent successfully", self.sender_email, subject_line)


Log_Format = "%(levelname)s %(name)s %(asctime)s: %(message)s"
logging.basicConfig(stream=sys.stdout,
                    filemode="w",
                    format=Log_Format,
                    level=config('TASKW_EMAIL_LOG_LEVEL', cast=int, default=logging.ERROR))
log = logging.getLogger("taskw-email")

MAIL_SERVER = config('TASKW_EMAIL_MAIL_SERVER')
USERNAME = config('TASKW_EMAIL_USERNAME')
PASSWORD = config('TASKW_EMAIL_PASSWORD')
SENDER_EMAIL = config('TASKW_EMAIL_SENDER_EMAIL')
SMTP_PORT = config('TASKW_EMAIL_SMTP_PORT', cast=int, default=465)
TASK_KEYWORD = "task:"
REPLY_PREFIX_EXPR = "(re: )*"
TASK_RE_MATCHER = re.compile(REPLY_PREFIX_EXPR + TASK_KEYWORD, re.IGNORECASE)
TASKCMD_KEYWORD = "taskcmd:"
TASKCMD_RE_MATCHER = re.compile(REPLY_PREFIX_EXPR + TASKCMD_KEYWORD, re.IGNORECASE)

taskw = TaskWarriorCmdLine()
for task_line in TaskEmails(MAIL_SERVER, USERNAME, PASSWORD, SENDER_EMAIL):
    log.debug("Task line is: ******* %s", task_line)

    response = taskw.process_line(task_line)
    log.debug("Task Warrior said: ** %s", response)

    email_response = EmailResponse(MAIL_SERVER, SMTP_PORT, USERNAME, PASSWORD, SENDER_EMAIL, task_line)
    email_response.add_response(response)
    email_response.send_response()
