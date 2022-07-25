from unittest.mock import MagicMock

from taskw_email import task_warrior_cmd_line
from taskw_email.task_warrior_cmd_line import TaskWarriorCmdLine
from subprocess import CompletedProcess


positive_task_line_matches = [
    ('task: hello', 'hello'),
    ('tasK: yessss!', 'yessss!'),
    ('Task: Yo how are things?', 'Yo how are things?'),
    ('TASK: booyah', 'booyah'),
    ('task: task: task task: task task task', 'task: task task: task task task'),
    ('re: task: hello', 'hello'),
    ('RE: re: tasK: yessss!', 'yessss!'),
    ('fw: Task: Yo how are things?', 'Yo how are things?'),
    ('FW: Task: Yo how are things?', 'Yo how are things?'),
    ('FWD: TASK: booyah', 'booyah'),
    ('re: fwd: task: task: task task: task task task', 'task: task task: task task task'),
    ('re: fw: task: task: task task: task task task', 'task: task task: task task task'),
]

negative_task_line_matches = [
    'ttask: maybe',
    'taks: no',
    'task hello',
    'this is a test of task: matching'
]


def test_various_matcher_use_cases():
    matcher = task_warrior_cmd_line.TASK_RE_MATCHER
    for (test_string, expected) in positive_task_line_matches:
        result = matcher.search(test_string)
        assert result, 'Should have matched on %s' % test_string
        (_ignore, index) = result.span()
        assert test_string[index:] == expected

    for test_string in negative_task_line_matches:
        assert not matcher.search(test_string)


def test_process_line_for_tasks():
    lines = [
        'task: hello world'
    ]

    task_warrior_cmd_line.TASKW_PATH = 'no_exec'
    taskcmd = MagicMock(spec=task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd)
    task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd = taskcmd
    twcl = TaskWarriorCmdLine()
    for line in lines:
        taskcmd.return_value = 'booya'
        assert twcl.process_line(line) == 'booya'
        taskcmd.assert_called_once()
        # I actually want to use assert_called_with but for inexplicable reasons it is not working


def test_process_line_for_taskcmds():
    lines = [
        'taskcmd: next',
    ]

    task_warrior_cmd_line.TASKW_PATH = 'no_exec'
    taskcmd = MagicMock(spec=task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd)
    task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd = taskcmd
    twcl = TaskWarriorCmdLine()
    for line in lines:
        taskcmd.return_value = 'booya'
        assert twcl.process_line(line) == 'booya'
        taskcmd.assert_called_once()
        # I actually want to use assert_called_with but for inexplicable reasons it is not working


def test_process_line_for_unknowns():
    lines = [
        'blah',
        'too bad',
        're:explosive growth',
        'broohahahahahahaha task:',
    ]

    task_warrior_cmd_line.TASKW_PATH = 'no_exec'
    task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd = MagicMock(spec=task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd)
    twcl = TaskWarriorCmdLine()
    for line in lines:
        task_warrior_cmd_line.TaskWarriorCmdLine.task_cmd.return_value = 'yo!'
        assert twcl.process_line(line) == 'Couldn\'t figure out what to do with %s' % line
