# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018-2022 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
from pathlib import Path


def get_file_modified_unixtime(pathname: Path) -> float:
    return pathname.stat().st_mtime
