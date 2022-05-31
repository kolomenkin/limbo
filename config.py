# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018-2022 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
import os
from pathlib import Path


def read_env(name: str, default_value: str) -> str:
    if name in os.environ:
        return os.environ[name]
    return default_value


WEB_SERVER = read_env('LIMBO_WEB_SERVER', 'wsgiref')

LISTEN_HOST = read_env('LIMBO_LISTEN_HOST', '127.0.0.1')
LISTEN_PORT = int(read_env('LIMBO_LISTEN_PORT', '8080'))

STORAGE_DIRECTORY = Path(read_env('LIMBO_STORAGE_DIRECTORY', './storage'))

# STORAGE_WEB_URL_BASE allows to specify alternative web url to
# read files stored in STORAGE_DIRECTORY through HTTP/HTTPS.
# It is expected those URL is served by standalone web server.
# Optional setting, empty string disables this setting.
# NOTE: value requires ending '/' character
STORAGE_WEB_URL_BASE = read_env('LIMBO_STORAGE_WEB_URL_BASE', '')

MAX_STORAGE_SECONDS = int(read_env('LIMBO_MAX_STORAGE_SECONDS', str(24 * 3600)))

IS_DEBUG = bool(int(read_env('LIMBO_IS_DEBUG', '0')))

DISABLE_STORAGE = bool(int(read_env('LIMBO_DISABLE_STORAGE', '0')))
