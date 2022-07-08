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
        cmdline = [self.taskw, 'sync']
        result = run(cmdline, shell=False, capture_output=True)
        log.debug("task sync returned %s - %s%s", result.returncode, result.stdout.decode(), result.stderr.decode())

    def process_line(self, task_line):
        task_line = task_line.strip()
        matcher = TASKCMD_RE_MATCHER.search(task_line)
        if matcher:
            return "taskcmd not yet implemented (%s)" % task_line
        matcher = TASK_RE_MATCHER.search(task_line)
        if matcher:
            (_ignore, index) = matcher.span()
            return self.add_task(task_line[index:])
        else:
            return "Couldn't figure out what to do with %s" % task_line

    def add_task(self, task_line):
        cmdline = [self.taskw, 'add'] + task_line.split()
        result = run(cmdline, shell=False, capture_output=True)
        response = "%s%s (%s)" % (result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode)
        log.debug("task add %s - response is %s", task_line, response)
        return response


TASK_RE_MATCHER = re.compile("(?P<all>^( *Re: *)*Task:)", re.IGNORECASE)
TASKCMD_RE_MATCHER = re.compile("(?P<all>^( *Re: *)*Taskcmd:)", re.IGNORECASE)
