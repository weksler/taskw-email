from .cfg import TASKW_PATH
from .cfg import log
import re
from subprocess import run


class TaskWarriorCmdLine:
    """Sends a command to task warrior by invoking the executable, and returns task warrior's response."""

    def __init__(self):
        if TASKW_PATH:
            self.taskw = TASKW_PATH
        else:
            result = run("which task", shell=True, capture_output=True)
            if result.returncode != 0:
                log.critical("Failed to find taskw executable.")
                raise RuntimeError
            self.taskw = result.stdout.strip().decode()
        log.debug("Task warrior executable is %s", self.taskw)

    def __del__(self):
        result = self.task_cmd('sync')
        log.debug("task sync returned %s - %s%s", result.returncode, result.stdout.decode(), result.stderr.decode())

    def process_line(self, task_line):
        task_line = task_line.strip()
        matcher = TASKCMD_RE_MATCHER.search(task_line)
        if matcher:
            (_ignore, index) = matcher.span()
            return self.task_cmd(task_line[index:])

        matcher = TASK_RE_MATCHER.search(task_line)
        if matcher:
            (_ignore, index) = matcher.span()
            return self.add_task(task_line[index:])

        return "Couldn't figure out what to do with %s" % task_line

    def add_task(self, task_line):
        return self.task_cmd("add %s" % task_line)

    def task_cmd(self, command):
        cmdline = [self.taskw] + command.split()
        result = run(cmdline, shell=False, capture_output=True)
        response = "%s%s (%s)" % (result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode)
        log.debug("task warrior command: %s - response is %s", command, response)
        return response


TASK_RE_MATCHER = re.compile("(?P<all>^( *(re|fw|fwd): *)*task: ?)", re.IGNORECASE)
TASKCMD_RE_MATCHER = re.compile("(?P<all>^( *(re|fw|fwd): *)*taskcmd: ?)", re.IGNORECASE)
