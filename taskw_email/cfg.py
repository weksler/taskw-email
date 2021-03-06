from decouple import config
import logging.handlers
import logging
import sys

# Setup logging to stdout and syslog
log_format = "%(levelname)s %(name)s[%(process)d] %(asctime)s: %(message)s"
logging.basicConfig(stream=sys.stdout,
                    filemode="w",
                    format=log_format,
                    level=config('TASKW_EMAIL_LOG_LEVEL', cast=int, default=logging.ERROR))
log = logging.getLogger("taskw-email")
sys_log_handler = logging.handlers.SysLogHandler(
    address=config('TASKW_EMAIL_SYS_LOG_PATH', cast=str, default='/dev/log'))
sys_log_handler.setFormatter(logging.Formatter(log_format))
log.addHandler(sys_log_handler)

# Load up config values from `.env`, and where appropriate, set defaults
MAIL_SERVER = config('TASKW_EMAIL_MAIL_SERVER')
USERNAME = config('TASKW_EMAIL_USERNAME')
PASSWORD = config('TASKW_EMAIL_PASSWORD')
SENDER_EMAIL = config('TASKW_EMAIL_SENDER_EMAIL')
SMTP_PORT = config('TASKW_EMAIL_SMTP_PORT', cast=int, default=465)
TASKW_PATH = config('TASKW_EMAIL_TASKW_PATH', default=None)
