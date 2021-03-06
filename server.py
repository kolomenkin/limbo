#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)

import config

from lib_file_storage import FileStorage
from lib_common import log, get_file_modified_unixtime

import bottle
from json import dumps as json_dumps
import mimetypes
from os import path as os_path
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import BaseTarget, NullTarget
from time import time as time_time
from urllib.parse import quote as urllib_quote


# ==========================================
# There are 4 types of file names:
# 1) Original file name provided by user
# 2) URL file name for use in URLs
# 3) Disk file name (on server)
# 4) Display name. Used on web page and to save file on end user's computer
# ==========================================


bottle.TEMPLATE_PATH = [os_path.join(os_path.dirname(__file__),
                                     'static', 'templates')]

STORAGE_URL_SUBDIR = '/files/'
URLPREFIX = STORAGE_URL_SUBDIR if config.STORAGE_WEB_URL_BASE == '' \
                               else config.STORAGE_WEB_URL_BASE

storage = FileStorage(config.STORAGE_DIRECTORY, config.MAX_STORAGE_SECONDS)


def format_size(b):
    if b < 10000:
        return '%i' % b + ' B'
    elif 10000 <= b < 10000000:
        return '%.0f' % float(b/1000) + ' KB'
    elif 10000000 <= b < 10000000000:
        return '%.0f' % float(b/1000000) + ' MB'
    elif 10000000000 <= b < 10000000000000:
        return '%.0f' % float(b/1000000000) + ' GB'
    elif 10000000000000 <= b:
        return '%.0f' % float(b/1000000000000) + ' TB'


def format_age(a):
    if a < 120:
        return '%is' % (a)
    a = a / 60
    if a < 60:
        return '%i m' % (a)
    if a < 60:
        return '%i m' % (a)
    return '%ih %im' % (a / 60, a % 60)


@bottle.route('/')
@bottle.view('root.html')
def root_page():
    log('Root page is requested')
    files = []
    items = storage.enumerate_files()
    now = time_time()
    for item in items:
        full_disk_filename = item['full_disk_filename']
        url_filename = item['url_filename']
        display_filename = item['display_filename']
        modified_unixtime = get_file_modified_unixtime(full_disk_filename)
        files.append(
            {
                'display_filename': display_filename,
                'url': URLPREFIX + urllib_quote(url_filename),
                'url_filename': url_filename,
                'size': format_size(os_path.getsize(full_disk_filename)),
                'age': format_age(now - modified_unixtime),
                'sortBy': now - modified_unixtime,
            })
    files = sorted(files, key=lambda item: item['sortBy'])
    return {
            'title': 'Limbo: the file sharing lightweight service',
            'h1': 'Limbo. The file sharing lightweight service',
            'files': files,
        }


# JSON API for auto tests and automation
@bottle.get('/cgi/enumerate/')
def cgi_enumerate():
    log('Enumerate files')
    bottle.response.content_type = 'application/json'
    files = []
    items = storage.enumerate_files()
    for item in items:
        full_disk_filename = item['full_disk_filename']
        url_filename = item['url_filename']
        display_filename = item['display_filename']
        modified_unixtime = get_file_modified_unixtime(full_disk_filename)
        files.append(
            {
                'display_filename': display_filename,
                'url': URLPREFIX + urllib_quote(url_filename),
                'url_filename': url_filename,
                'size': os_path.getsize(full_disk_filename),
                'modified': modified_unixtime,
            })
    files = sorted(files, key=lambda item: item['modified'])
    return json_dumps(files, indent=4)


@bottle.post('/cgi/addtext/')
def cgi_addtext():
    text_title = bottle.request.forms.title
    log('Share text begin: ' + text_title)
    original_filename = text_title + '.txt'
    body = bytearray(bottle.request.forms.body, encoding='utf-8')

    with storage.open_file_writer(original_filename) as writer:
        writer.write(body)

    log('Shared text size: ' + str(len(body)))
    return 'OK'


class StorageFileTarget(BaseTarget):
    def __init__(self):
        super().__init__()
        self._writer = None

    def start(self):
        self._writer = storage.open_file_writer(self.multipart_filename)

    def data_received(self, chunk):
        self._writer.write(chunk)

    def finish(self):
        self._writer.close()


@bottle.post('/cgi/upload/')
def cgi_upload():
    log('Upload file begin')

    use_async_implementation = True

    if use_async_implementation:
        size = 0
        file = NullTarget() if config.DISABLE_STORAGE else StorageFileTarget()
        parser = StreamingFormDataParser(headers=bottle.request.headers)
        parser.register('file', file)

        while True:
            chunk = bottle.request.environ['wsgi.input'].read(64 * 1024)
            if not chunk:
                break
            parser.data_received(chunk)
            size += len(chunk)

        log('Uploaded request size: ' + str(size))
    else:
        size = 0
        upload = bottle.request.files.get('file')
        if upload is None:
            raise Exception('ERROR! "file" multipart field was not found')
        original_filename = upload.raw_filename
        body = upload.file

        with storage.open_file_writer(original_filename) as writer:
            while True:
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                if not config.DISABLE_STORAGE:
                    writer.write(chunk)
                size += len(chunk)

        log('Uploaded file size: ' + str(size))
    return 'OK'


@bottle.post('/cgi/remove/')
def cgi_remove():
    log('Remove file begin')
    urlpath = bottle.request.forms.fileName
    storage.remove_file(urlpath)
    return 'OK'


# API endpoint for auto tests
@bottle.post('/cgi/remove-all/')
def cgi_remove_all():
    log('Remove all files in storage')
    storage.remove_all_files()
    return 'OK'


@bottle.route('/static/<urlpath:path>')
def server_static(urlpath):
    # log('Static file requested: ' + urlpath)
    root_folder = os_path.abspath(os_path.dirname(__file__))
    response = bottle.static_file(urlpath,
                                  root=os_path.join(root_folder, 'static'))
    response.set_header('Cache-Control', 'public, max-age=604800')
    return response


@bottle.route('/favicon.ico')
def server_favicon():
    return server_static('favicon.png')


@bottle.route(STORAGE_URL_SUBDIR + '<url_filename>')
def server_storage(url_filename):
    log('File download: ' + url_filename)
    filedir, disk_filename, display_filename = \
        storage.get_file_info_to_read(url_filename)

    # show preview for images and text files
    # force text files to be shown as text/plain
    # (and not text/html for example)

    # Empty extenstion is treated as .txt extension
    mime_filename = display_filename \
        if '.' in display_filename else display_filename + '.txt'

    mimetype, encoding = mimetypes.guess_type(mime_filename)
    mimetype = str(mimetype)
    if mimetype.startswith('text/'):
        mimetype = 'text/plain'
    elif not mimetype.startswith('image/'):
        mimetype = ''
    showpreview = mimetype != ''
    quoted_display_filename = urllib_quote(display_filename)

    if showpreview:
        response = bottle.static_file(disk_filename,
                                      root=filedir,
                                      mimetype=mimetype)
        content_disposition = 'inline; filename="%s"' % \
            quoted_display_filename
        response.set_header('Content-Disposition', content_disposition)
    else:
        response = bottle.static_file(disk_filename,
                                      root=filedir,
                                      download=quoted_display_filename)

    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')
    return response


if __name__ == '__main__':
    log('Loading...')

    # treat more file extensions as text files
    # (so preview in browser will be available)
    for ext in [
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
            ]:
        mimetypes.add_type('text/' + ext, '.' + ext)

    storage.start()

    log('Start server...')

    bottle.run(app=bottle.app(),
               server=config.WEB_SERVER,
               host=config.LISTEN_HOST,
               port=config.LISTEN_PORT,
               debug=config.IS_DEBUG)

    log('Unloading...')
    storage.stop()
    log('Unloaded')
