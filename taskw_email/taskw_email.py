import cfg
from cfg import log
from incoming_task_emails import IncomingTaskEmails
from task_warrior_cmd_line import TaskWarriorCmdLine
from email_response import EmailResponse

taskw = TaskWarriorCmdLine()
for task_line in IncomingTaskEmails(cfg.MAIL_SERVER, cfg.USERNAME, cfg.PASSWORD, cfg.SENDER_EMAIL):
    log.debug("Task line is: ******* %s", task_line)

    response = taskw.process_line(task_line)
    log.debug("Task Warrior said: ** %s", response)

    email_response = EmailResponse(cfg.MAIL_SERVER, cfg.SMTP_PORT, cfg.USERNAME, cfg.PASSWORD, cfg.SENDER_EMAIL, task_line)
    email_response.add_response(response)
    email_response.send_response()
