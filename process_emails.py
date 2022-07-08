from taskw_email import cfg
from taskw_email.incoming_task_emails import IncomingTaskEmails
from taskw_email.task_warrior_cmd_line import TaskWarriorCmdLine
from taskw_email.email_response import EmailResponse
import imaplib

imap_connection = imaplib.IMAP4_SSL(cfg.MAIL_SERVER)
taskw = TaskWarriorCmdLine()
for task_line in IncomingTaskEmails(cfg.USERNAME, cfg.PASSWORD, cfg.SENDER_EMAIL, imap_connection):
    cfg.log.debug("Task line is: ******* %s", task_line)

    response = taskw.process_line(task_line)
    cfg.log.debug("Task Warrior said: ** %s", response)

    email_response = EmailResponse(cfg.MAIL_SERVER, cfg.SMTP_PORT, cfg.USERNAME, cfg.PASSWORD, cfg.SENDER_EMAIL,
                                   task_line)
    email_response.add_response(response)
    email_response.send_response()
