#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)

import config

from lib_file_storage import FileStorage
from lib_common import log, file_age_in_seconds

import bottle
import mimetypes
import os
from urllib.parse import quote

bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__),
                                     'static', 'templates')]

STORAGE_URL_SUBDIR = '/files/'

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
    urlprefix = STORAGE_URL_SUBDIR if config.STORAGE_WEB_URL_BASE == '' \
                                   else config.STORAGE_WEB_URL_BASE
    files = []
    items = storage.enumerate_files()
    for item in items:
        fullname = item['fulldiskname']
        urlname = item['urlname']
        displayname = item['displayname']
        age = file_age_in_seconds(fullname)
        files.append(
            {
                'name': displayname,
                'url': urlprefix + quote(urlname),
                'urlname': urlname,
                'size': format_size(os.path.getsize(fullname)),
                'age': format_age(age),
                'sortBy': age,
            })
    return {
            'title': 'Limbo: the file sharing lightweight service',
            'h1': 'Limbo. The file sharing lightweight service',
            'files': sorted(files, key=lambda item: item['sortBy']),
        }


@bottle.post('/cgi/addtext/')
def cgi_addtext():
    log('Share text begin')
    filename = bottle.request.forms.title + '.txt'
    body = bytearray(bottle.request.forms.body, encoding='utf-8')

    with storage.open_file_to_write(filename) as file:
        file.write(body)

    log('Shared text size: ' + str(len(body)))
    return 'OK'


@bottle.post('/cgi/upload/')
def cgi_upload():
    log('Upload file begin')
    upload = bottle.request.files.get('file')
    filename = upload.raw_filename
    body = upload.file
    size = 0

    with storage.open_file_to_write(filename) as file:
        while True:
            chunk = body.read(64 * 1024)
            if not chunk:
                break
            file.write(chunk)
            size += len(chunk)

    log('Uploaded file size: ' + str(size))
    return 'OK'


@bottle.post('/cgi/remove/')
def cgi_remove():
    log('Remove file begin')
    filename = bottle.request.forms.fileName
    storage.remove_file(filename)
    return 'OK'


@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    log('Static file requested: ' + filepath)
    root_folder = os.path.abspath(os.path.dirname(__file__))
    response = bottle.static_file(filepath,
                                  root=os.path.join(root_folder, 'static'))
    response.set_header('Cache-Control', 'public, max-age=604800')
    return response


@bottle.route('/favicon.ico')
def server_favicon():
    return server_static('favicon.png')


@bottle.route(STORAGE_URL_SUBDIR + '<filepath:path>')
def server_storage(filepath):
    log('File download: ' + filepath)
    filedir, filename = storage.get_file_info_to_read(filepath)

    # show preview for images and text files
    # force text files to be shown as text/plain
    # (and not text/html for example)

    mimetype, encoding = mimetypes.guess_type(filename)
    mimetype = str(mimetype)
    if mimetype.startswith('text/'):
        mimetype = 'text/plain'
    elif not mimetype.startswith('image/'):
        mimetype = ''
    showpreview = mimetype != ''

    if showpreview:
        response = bottle.static_file(filename,
                                      root=filedir, mimetype=mimetype)
    else:
        response = bottle.static_file(filename,
                                      root=filedir, download=filepath)

    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')
    return response


if __name__ == '__main__':
    log('Loading...')

    # treat more file extensions as test files
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
