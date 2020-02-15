#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
import json
import logging
import mimetypes
import os
import sys
import urllib
from time import time
from typing import Dict, Any, Optional

from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import BaseTarget, NullTarget
import bottle

import config
from lib_bottle import bottle_get, bottle_post, bottle_route, bottle_view, RouteResponse
from lib_common import get_file_modified_unixtime
from lib_file_storage import FileStorage, StorageFileItem, AtomicFile

ViewResponse = Dict[str, Any]
MethodResponse = str

LOGGER = logging.getLogger('app')

# ==========================================
# There are 4 types of file names:
# 1) Original file name provided by user
# 2) URL file name for use in URLs
# 3) Disk file name (on server)
# 4) Display name. Used on web page and to save file on end user's computer
# ==========================================

STORAGE_URL_SUBDIR = '/files/'
URLPREFIX = config.STORAGE_WEB_URL_BASE or STORAGE_URL_SUBDIR

STORAGE = FileStorage(config.STORAGE_DIRECTORY, config.MAX_STORAGE_SECONDS)


def format_size(size: int) -> str:
    kib = 1024
    mib = kib * kib
    gib = kib * kib * kib
    tib = kib * kib * kib * kib

    if size < 10 * kib:
        return f'{size} B'
    if size < 10 * mib:
        return f'{size/kib:.1f} KiB'
    if size < 10 * gib:
        return f'{size/mib:.1f} MiB'
    if size < 10 * tib:
        return f'{size/gib:.1f} GiB'
    return f'{size/tib:.1f} TiB'


def format_age(seconds: int) -> str:
    if seconds < 120:
        return f'{seconds}s'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes}m'
    return '{minutes // 60}h {minutes % 60}m'


@bottle_route('/')
@bottle_view('root.html')
def root_page() -> ViewResponse:
    LOGGER.info('Root page is requested')
    result_files = []
    files = STORAGE.enumerate_files()
    now = time()
    for file in files:
        modified_unixtime = get_file_modified_unixtime(file.full_disk_filename)
        result_files.append(
            {
                'display_filename': file.display_filename,
                'url': URLPREFIX + urllib.parse.quote(file.url_filename),
                'url_filename': file.url_filename,
                'size': format_size(os.path.getsize(file.full_disk_filename)),
                'age': format_age(int(now - modified_unixtime)),
                'sortBy': now - modified_unixtime,
            }
        )
    result_files = sorted(result_files, key=lambda item: item['sortBy'])
    return {
        'title': 'Limbo: the file sharing lightweight service',
        'h1': 'Limbo. The file sharing lightweight service',
        'files': result_files,
    }


# JSON API for auto tests and automation
@bottle_get('/cgi/enumerate/')
def cgi_enumerate() -> MethodResponse:
    LOGGER.info('Enumerate result_files')
    bottle.response.content_type = 'application/json'
    result_files = []
    files = STORAGE.enumerate_files()
    for file in files:
        modified_unixtime = get_file_modified_unixtime(file.full_disk_filename)
        result_files.append(
            {
                'display_filename': file.display_filename,
                'url': URLPREFIX + urllib.parse.quote(file.url_filename),
                'url_filename': file.url_filename,
                'size': os.path.getsize(file.full_disk_filename),
                'modified': modified_unixtime,
            }
        )
    result_files = sorted(result_files, key=lambda item: item['modified'])
    return json.dumps(result_files, indent=4)


@bottle_post('/cgi/addtext/')
def cgi_addtext() -> MethodResponse:
    forms: bottle.FormsDict = bottle.request.forms
    text_title = forms.title  # pylint: disable=no-member
    LOGGER.info('Share text begin: %s', text_title)
    original_filename = text_title + '.txt'
    body = bytearray(forms.body, encoding='utf-8')  # pylint: disable=no-member

    with STORAGE.open_file_writer(original_filename) as writer:
        writer.write(body)

    LOGGER.info('Shared text size: %d', len(body))
    return 'OK'


class StorageFileTarget(BaseTarget):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self._writer: Optional[AtomicFile] = None

    def on_start(self) -> None:
        LOGGER.debug('StorageFileTarget: on_start')
        self._writer = STORAGE.open_file_writer(self.multipart_filename)

    def on_data_received(self, chunk: bytes) -> None:
        LOGGER.debug('StorageFileTarget: on_data_received: %d bytes', len(chunk))
        assert self._writer is not None
        self._writer.write(chunk)

    def on_finish(self) -> None:
        LOGGER.debug('StorageFileTarget: on_finish')
        assert self._writer is not None
        self._writer.close()


@bottle_post('/cgi/upload/')
def cgi_upload() -> MethodResponse:
    LOGGER.info('Upload file begin')

    # wsgiref does not support async reading from environ['wsgi.input']
    # It blocks forever in read(size) call.
    use_async_implementation = config.WEB_SERVER != 'wsgiref'

    if use_async_implementation:
        size = 0
        file = NullTarget() if config.DISABLE_STORAGE else StorageFileTarget()
        parser = StreamingFormDataParser(headers=bottle.request.headers)
        parser.register('file', file)

        while True:
            LOGGER.debug('Read async chunk...')
            buffer = bottle.request.environ['wsgi.input']
            chunk = buffer.read(64 * 1024)
            if not chunk:
                break
            LOGGER.debug('Got async chunk from network: %d bytes', len(chunk))
            parser.data_received(chunk)
            size += len(chunk)

        LOGGER.info('Uploaded request size: %s bytes', size)
    else:
        size = 0
        files: bottle.FormsDict = bottle.request.files
        upload = files.file  # pylint: disable=no-member
        if upload is None:
            raise Exception('ERROR! "file" multipart field was not found')
        original_filename = upload.raw_filename
        body = upload.file

        with STORAGE.open_file_writer(original_filename) as writer:
            while True:
                LOGGER.debug('Read synchronous chunk...')
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                LOGGER.debug('Got synchronous chunk from network: %d bytes', len(chunk))
                if not config.DISABLE_STORAGE:
                    writer.write(chunk)
                size += len(chunk)

        LOGGER.info('Uploaded file size: %d bytes', size)
    return 'OK'


@bottle_post('/cgi/remove/')
def cgi_remove() -> MethodResponse:
    LOGGER.info('Remove file begin')
    forms: bottle.FormsDict = bottle.request.forms
    urlpath = forms.fileName  # pylint: disable=no-member
    STORAGE.remove_file(urlpath)
    return 'OK'


# API endpoint for auto tests
@bottle_post('/cgi/remove-all/')
def cgi_remove_all() -> MethodResponse:
    LOGGER.info('Remove all files in storage')
    STORAGE.remove_all_files()
    return 'OK'


@bottle_route('/static/<urlpath:path>')
def server_static(urlpath: str) -> RouteResponse:
    LOGGER.debug('Static file requested: %s', urlpath)
    root_folder = os.path.abspath(os.path.dirname(__file__))
    response = bottle.static_file(urlpath, root=os.path.join(root_folder, 'static'))
    response.set_header('Cache-Control', 'public, max-age=604800')
    return response


@bottle_route('/favicon.ico')
def server_favicon() -> RouteResponse:
    return server_static('favicon.png')


@bottle_route(STORAGE_URL_SUBDIR + '<url_filename>')
def server_storage(url_filename: str) -> RouteResponse:
    LOGGER.info('File download: %s', url_filename)
    info: StorageFileItem = STORAGE.get_file_info_to_read(url_filename)

    # show preview for images and text files
    # force text files to be shown as text/plain
    # (and not text/html for example)

    # Missing extension is treated as .txt extension
    mime_filename = info.display_filename if '.' in info.display_filename else info.display_filename + '.txt'

    mimetype, _ = mimetypes.guess_type(mime_filename)
    mimetype = str(mimetype)
    if mimetype.startswith('text/'):
        mimetype = 'text/plain'
    elif not mimetype.startswith('image/'):
        mimetype = ''
    showpreview = mimetype != ''
    quoted_display_filename = urllib.parse.quote(info.display_filename)

    if showpreview:
        response = bottle.static_file(
            info.disk_filename,
            root=info.storage_directory,
            mimetype=mimetype,
        )
        content_disposition = 'inline; filename="%s"' % \
            quoted_display_filename
        response.set_header('Content-Disposition', content_disposition)
    else:
        response = bottle.static_file(
            info.disk_filename,
            root=info.storage_directory,
            download=quoted_display_filename,
        )

    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')
    return response


def main() -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG if config.IS_DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    LOGGER.info('Loading...')

    # treat more file extensions as text files
    # (so preview in browser will be available)
    for ext in {
            'cfg',
            'cmake',
            'cmd',
            'conf',
            'ini',
            'json',
            'log',
            'man',
            'md',
            'php',
            'sh',
    }:
        mimetypes.add_type(f'text/{ext}', f'.{ext}')

    STORAGE.start()

    LOGGER.info('Start server...')

    bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__), 'static', 'templates')]

    bottle.run(app=bottle.app(),
               server=config.WEB_SERVER,
               host=config.LISTEN_HOST,
               port=config.LISTEN_PORT,
               debug=config.IS_DEBUG)

    LOGGER.info('Unloading...')
    STORAGE.stop()
    LOGGER.info('Unloaded')


if __name__ == '__main__':
    main()
