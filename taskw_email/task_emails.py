from cfg import log
import email
import imaplib

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
