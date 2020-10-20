"""
A simple Git blame plugin. Outputs to the status bar the author of, and
time since, the current line's last edit.
Inspiration: https://raw.githubusercontent.com/rodrigobdz/subl-gitblame-statusbar/master/git_blame_sublime_statusbar.py
"""

import os
import subprocess
from subprocess import check_output
from datetime import datetime
from math import floor
import re
import sublime
import sublime_plugin

YOU = 'You'


def parse_blame(blame):
    """
    Gets the username and date from Git blame output.

    :param      blame:  Git blame output.
    :type       blame:  str

    :returns:   User and date last edited.
    :rtype:     Tuple[str, str]
    """
    user, date = '', ''

    # match full date and time (ISO date pattern)
    # datetime_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    # match relative datetime
    datetime_pattern = r'\d+\s\w+\sago'
    # match user name, preceded by `(`, and followed by a date
    user_pattern = rf'(?<=\()[\w\- ]+(?=({datetime_pattern}))'
    # match the user name when a line change has not been committed yet
    not_committed_pattern = 'Not Committed Yet'

    user_match = re.search(user_pattern, blame)
    not_committed_match = re.search(not_committed_pattern, blame)
    datetime_match = re.search(datetime_pattern, blame)

    if datetime_match:
        date = datetime_match.group(0).strip()
    if not_committed_match:
        user = YOU
    elif user_match:
        user = user_match.group(0).strip()

    return (user, date)


def get_blame(line, path):
    """
    Gets blame information for the current line.

    :param      line:  Line number in file.
    :type       line:  str
    :param      path:  Path to current file.
    :type       path:  str

    :returns:   Git blame output.
    :rtype:     str
    """
    try:
        return check_output(['git', 'blame', '--minimal', '--date=relative',
                             '-L {0},{0}'.format(line), path],
                            cwd=os.path.dirname(os.path.realpath(path)),
                            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pass
        # print('Git blame: git error {}:\n{}'.format(e.returncode, e.output.decode('UTF-8')))
    except Exception as e:
        pass
        # print('Git blame: Unexpected error:', e)
    return ''


def get_current_user(path):
    """
    Gets the current Git user.

    :param      path:  Path to current file.
    :type       path:  str

    :returns:   The current user.
    :rtype:     str
    """
    try:
        return check_output(['git', 'config', 'user.name'],
                            cwd=os.path.dirname(os.path.realpath(path)),
                            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pass
        # print('Git blame: git error {}:\n{}'.format(e.returncode, e.output.decode('UTF-8')))
    except Exception as e:
        pass
        # print('Git blame: Unexpected error:', e)
    return ''


def time_between(date):
    """
    Returns the string message of how much time has elapsed since the last edit.

    :param      date:  Date of edit
    :type       date:  str

    :returns:   Time since last edit.
    :rtype:     str
    """
    now = datetime.now()
    blame_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    delta = now - blame_date

    minutes = floor(abs(delta.seconds / 60))
    hours = round(abs(delta.seconds / 60 / 60))
    days = round(abs(delta.days) + (abs(delta.seconds) / 60 / 60 / 24))
    weeks = round(abs(days / 7))
    months = round(abs(days / 30))
    years = round(abs(delta.days / 365))

    # use 'years' arond the two-year mark
    if months > 24:
        return "{0} {1} ago".format(years, 'years' if years > 1 else 'year')
    # use 'months' around the two-month mark
    if days > 60:
        return "{0} {1} ago".format(months, 'months' if months > 1 else 'month')
    # use 'weeks' around the four-week mark
    if days > 28:
        return "{0} {1} ago".format(weeks, 'weeks' if weeks > 1 else 'week')
    if days > 0:
        return "{0} {1} ago".format(days, 'days' if days > 1 else 'day')
    if hours > 0:
        return "{0} {1} ago".format(hours, 'hours' if hours > 1 else 'hour')
    if minutes > 0:
        return "{0} {1} ago".format(minutes, 'minutes' if minutes > 1 else 'minute')

    return "a few seconds ago"


def update_status_bar(view):
    """
    Updates the status bar with the current line's Git blame info.

    :type       view:  sublime.View
    """
    try:
        row, _ = view.rowcol(view.sel()[0].begin())
        path = view.file_name()
        curr_user = get_current_user(path)
        blame = get_blame(int(row) + 1, path)
        output = ''

        if blame and curr_user:
            blame = blame.decode('utf-8')
            curr_user = curr_user.decode('utf-8').strip()
            user, date = parse_blame(blame)
            user = YOU if user == curr_user else user
            output = user + ", " + date

        view.set_status('git_blame', output)
    except:
        pass


class GitBlameStatusbarCommand(sublime_plugin.EventListener):
    """
    Plugin to update status bar view with Git blame information.
    """

    def on_load_async(self, view):
        """
        Update status bar when the file loads.
        """
        update_status_bar(view)

    def on_selection_modified_async(self, view):
        """
        Update status bar whenever the currently-selected line changes.
        """
        update_status_bar(view)