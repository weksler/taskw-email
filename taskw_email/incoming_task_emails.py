from .cfg import log
import email
from email.utils import parseaddr


class IncomingTaskEmails:
    """An iterator for retrieving emails from the inbox of an imap server, ignoring their content and
    only returning the subject line from the emails if they are from the specified sender_email.
    """

    def __init__(self, imap_user, imap_password, sender_email, imap_connection):
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.sender_email = sender_email
        self.imap_connection = imap_connection
        try:
            self.imap_connection.login(imap_user, imap_password)
            retcode, _ignore = self.imap_connection.enable("UTF8=ACCEPT")
            if retcode != 'OK':
                self.imap_connection.close()
                raise RuntimeError("Got error <" + retcode + "> when enabling UTF8")
        except Exception as e:
            log.critical("failed to connect as user %s (exception %s)", imap_user, e, exc_info=True)
            raise RuntimeError



    def __del__(self):
        try:
            self.imap_connection.close()
        except:
            None  # ignore

    def __iter__(self):
        retcode, messages = self.imap_connection.select("INBOX")
        if retcode != 'OK':
            self.imap_connection.close()
            raise RuntimeError("Got error <" + retcode + "> when selecting INBOX")
        log.debug("INBOX contains %s messages", int(messages[0]))
        return self

    def __next__(self):
        retcode, messages = self.imap_connection.search(None, '(UNSEEN)')
        if retcode != 'OK':
            log.critical("Error fetching unread messages - return code %s", retcode)
            raise StopIteration

        unread_messages = messages[0].decode('utf-8').strip().split()
        if len(unread_messages) == 0:
            log.debug("No unread messages.")
            raise StopIteration

        for unread_message_num in unread_messages:
            log.debug("Now processing message %s", unread_message_num)
            retcode, data = self.imap_connection.fetch(unread_message_num, '(RFC822)')
            if retcode != 'OK':
                log.critical("Error fetching message %s, return code %s", unread_message_num, retcode)
                raise StopIteration
            message_string = data[0][1].decode('utf-8')
            log.debug('Message is:\n--------\n%s\n---------\n', message_string)
            msg = email.message_from_string(message_string)
            sender = msg['From']
            subject = msg['Subject']
            log.debug("Message from %s with subject %s", sender, subject)
            if self.sender_email != parseaddr(sender)[1]:
                log.critical("Will not process tasks from %s", sender)
                continue

            return subject
