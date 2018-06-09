#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)

from os import stat as os_stat
from stat import ST_MTIME as stat_ST_MTIME
from time import strftime as time_strftime


def log(*args):
    print('DBG>', time_strftime('%Y-%m-%d %H:%M:%S:'), *args)


def get_file_modified_unixtime(pathname):
    return os_stat(pathname)[stat_ST_MTIME]
