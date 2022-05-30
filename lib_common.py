# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018-2022 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
import os
import stat


def get_file_modified_unixtime(pathname: str) -> float:
    return os.stat(pathname)[stat.ST_MTIME]
