import imaplib
import email
from decouple import config
import sys
import logging
from subprocess import run


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
        if task_line.startswith('taskcmd:'):
            return "taskcmd not yet implemented (%s)" % task_line
        elif task_line.startswith('task:'):
            return self.add_task(task_line[5:])
        else:
            return "Couldn't figure out what to do with %s" % task_line

    def add_task(self, task_line):
        cmdline = [self.taskw, 'add'] + task_line.split()
        result = run(cmdline, shell=False, capture_output=True)
        response = "%s%s (%s)" % (result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode)
        log.debug("task add %s - response is %s", task_line, response)
        return response


Log_Format = "%(levelname)s %(name)s %(asctime)s: %(message)s"
logging.basicConfig(stream=sys.stdout,
                    filemode="w",
                    format=Log_Format,
                    level=logging.DEBUG)
log = logging.getLogger("taskw-email")

taskw = TaskWarriorCmdLine()
for task_line in TaskEmails(config('TASKW_EMAIL_MAIL_SERVER'),
                            config('TASKW_EMAIL_USERNAME'),
                            config('TASKW_EMAIL_PASSWORD'),
                            config('TASKW_EMAIL_SENDER_EMAIL')):
    print("Task line is: *******", task_line)
    response = taskw.process_line(task_line)
    print("Task Warrior said: **", response)
