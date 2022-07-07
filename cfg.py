from decouple import config
import logging
import sys

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
