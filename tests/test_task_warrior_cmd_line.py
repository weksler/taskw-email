from taskw_email import task_warrior_cmd_line


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
