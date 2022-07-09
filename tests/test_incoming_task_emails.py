import pytest
from imaplib import IMAP4_SSL
from unittest.mock import MagicMock, call
from taskw_email.incoming_task_emails import IncomingTaskEmails


@pytest.fixture
def mock_imap_connection():
    return MagicMock(spec=IMAP4_SSL)


def test_bad_creds(mock_imap_connection):
    mock_imap_connection.login = MagicMock(side_effect=Exception("Oy vey!"))
    with pytest.raises(RuntimeError):
        IncomingTaskEmails("user", "password", "from@a.com", mock_imap_connection)


def test_no_inbox(mock_imap_connection):
    # Setup:
    # Login works
    mock_imap_connection.login.return_value = None
    # No inbox is found
    mock_imap_connection.select.return_value = ('NOT FOUND', -1)

    # Test:
    # Try to iterate
    with pytest.raises(RuntimeError) as e:
        for __ignore in IncomingTaskEmails("user", "password", "from@a.com", mock_imap_connection):
            assert False, "Should not have iterated"

    # Verify:
    # Ensure calls were actually made
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.close()
    ]


def test_can_fetch_unread_messages(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.return_value = ('ERROR', -1)

    # Test
    for email in IncomingTaskEmails("user", "password", "from@a.com", mock_imap_connection):
        assert False, "Should not have iterated"

    # Verify
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.close()
    ]


def test_no_unread_messages(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.return_value = ('OK', [b''])

    # Test
    for email in IncomingTaskEmails("user", "password", "from@a.com", mock_imap_connection):
        assert False, "Should not have iterated"

    # Verify
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.close()
    ]


def test_cant_fetch_message(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.return_value = ('OK', [b'2 6'])
    mock_imap_connection.fetch.return_value = ('FAILED', "")

    # Test
    for email in IncomingTaskEmails("user", "password", "from@a.com", mock_imap_connection):
        assert False, "Should not have iterated"

    # Verify
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.fetch("2", "(RFC822)"),
        call.close()
    ]


def test_message_wrong_sender(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.side_effect = [('OK', [b'2 6'])]
    mock_imap_connection.fetch.side_effect = [
        ('OK', [[
            None,
            (
                b'Content-Type: text/plain; charset="utf-8"\nContent-Transfer-Encoding: 7bit\n'
                b'MIME-Version: 1.0\nTo: to@x.com\nFrom: wrongsender@x.com\nSubject: Wrong Task Line'
                b'\n\nOh hello there!\n'
            )
        ]]),
        ('OK', [[
            None,
            (
                b'Content-Type: text/plain; charset="utf-8"\nContent-Transfer-Encoding: 7bit\n'
                b'MIME-Version: 1.0\nTo: to@x.com\nFrom: sender@x.com\nSubject: Task Line!'
                b'\n\nOh hello there!\n'
            )
        ]])
    ]

    # Test
    count = 0
    for task_line in IncomingTaskEmails("user", "password", "sender@x.com", mock_imap_connection):
        count += 1
        assert task_line == 'Task Line!'

    # Verify
    assert count == 1
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.fetch("2", "(RFC822)"),
        call.fetch("6", "(RFC822)"),
        call.search(None, "(UNSEEN)"),
        call.close()
    ]


def test_happy_path(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.side_effect = [('OK', [b'2']), ('OK', [b''])]
    mock_imap_connection.fetch.return_value = ('OK', [[
        None,
        (
            b'Content-Type: text/plain; charset="utf-8"\nContent-Transfer-Encoding: 7bit\n'
            b'MIME-Version: 1.0\nTo: to@x.com\nFrom: sender@x.com\nSubject: Task Line!'
            b'\n\nOh hello there!\n'
        )
    ]])

    # Test
    for task_line in IncomingTaskEmails("user", "password", "sender@x.com", mock_imap_connection):
        assert task_line == 'Task Line!'

    # Verify
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.fetch("2", "(RFC822)"),
        call.search(None, "(UNSEEN)"),
        call.close()
    ]


def test_happy_path_explicit_utf8(mock_imap_connection):
    # Setup:
    mock_imap_connection.login.return_value = None
    mock_imap_connection.select.return_value = ('OK', [b'25'])
    mock_imap_connection.search.side_effect = [('OK', [b'2']), ('OK', [b''])]
    mock_imap_connection.fetch.return_value = ('OK', [[
        None,
        (
            'Content-Type: text/plain; charset="utf-8"\nContent-Transfer-Encoding: 7bit\n'
            'MIME-Version: 1.0\nTo: to@x.com\nFrom: sender@x.com\nSubject: כגדשTask Line!'
            '\n\nOh hello there!\n'.encode('utf-8')
        )
    ]])

    # Test
    for task_line in IncomingTaskEmails("user", "password", "sender@x.com", mock_imap_connection):
        assert task_line == 'כגדשTask Line!'

    # Verify
    assert mock_imap_connection.mock_calls == [
        call.login("user", "password"),
        call.select("INBOX"),
        call.search(None, "(UNSEEN)"),
        call.fetch("2", "(RFC822)"),
        call.search(None, "(UNSEEN)"),
        call.close()
    ]
