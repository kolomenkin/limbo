#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)

import config

import bottle
import datetime
import io
import mimetypes
import os
import re
import stat
import sys
import time
import threading

bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__), 'static', 'templates')]
STORAGE_DIRECTORY = os.path.abspath(config.STORAGE_DIRECTORY)
STORAGE_URL_SUBDIR = '/files/'
STOP_THREADS = False

def log(*args):
    print('DBG>', time.strftime('%Y-%m-%d %H:%M:%S:'), *args)

def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]

def clean_filename(filename):
    s = re.sub('[\\\\:\'\\[\\]/",<>&^$+*?;]', '_', filename)
    s = re.sub('^(CON|PRN|AUX|NUL|COM\\d|LPT\\d)$', 'SPECIAL', s, flags=re.IGNORECASE)
    return s

def check_retention():
    for file in os.listdir(STORAGE_DIRECTORY):
        fullname = os.path.join(STORAGE_DIRECTORY, file)
        if os.path.isfile(fullname):
            if file_age_in_seconds(fullname) > config.MAX_STORAGE_SECONDS:
                log('Remove outdated file: ' + fullname)
                os.remove(fullname)

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
    urlprefix = STORAGE_URL_SUBDIR if config.STORAGE_WEB_URL_BASE == '' else config.STORAGE_WEB_URL_BASE
    files = []
    for file in os.listdir(STORAGE_DIRECTORY):
        fullname = os.path.join(STORAGE_DIRECTORY, file)
        if os.path.isfile(fullname):
            age = file_age_in_seconds(fullname)
            files.append(
            {
                'name': file,
                'url': urlprefix + file,
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
    title = bottle.request.forms.title
    body = bottle.request.forms.body
    fullname = os.path.join(STORAGE_DIRECTORY, clean_filename(title) + '.txt')
    log('Share text into: ' + fullname)
    with io.open(fullname, 'x', encoding='utf-8') as file:
        file.write(body)
    return 'OK'

@bottle.post('/cgi/upload/')
def cgi_upload():
    upload = bottle.request.files.get('file')
    fullname = os.path.join(STORAGE_DIRECTORY, clean_filename(upload.filename))
    log('Upload file: ' + fullname)
    upload.save(fullname)
    return 'OK'

@bottle.post('/cgi/remove/')
def cgi_remove():
    file = bottle.request.forms.fileName
    fullname = os.path.join(STORAGE_DIRECTORY, clean_filename(file))
    log('Remove file: ' + fullname)
    os.remove(fullname)
    return 'OK'

@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    root_folder = os.path.abspath(os.path.dirname(__file__))
    response = bottle.static_file(filepath, root=os.path.join(root_folder, 'static'))
    response.set_header('Cache-Control', 'public, max-age=604800')
    return response

@bottle.route('/favicon.ico')
def server_favicon():
    return server_static('favicon.png')

@bottle.route(STORAGE_URL_SUBDIR + '<filepath:path>')
def server_storage(filepath):
    filepath = clean_filename(filepath)

    # show preview for images and text files
    # force text files to be shown as text/plain (and not text/html for example)

    mimetype, encoding = mimetypes.guess_type(filepath)
    mimetype = str(mimetype)
    if mimetype.startswith('text/'):
        mimetype = 'text/plain'
    elif not mimetype.startswith('image/'):
        mimetype = ''
    showpreview = mimetype != ''

    if showpreview:
        response = bottle.static_file(filepath, root=STORAGE_DIRECTORY, mimetype=mimetype)
    else:
        response = bottle.static_file(filepath, root=STORAGE_DIRECTORY, download=filepath)

    response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.set_header('Pragma', 'no-cache')
    response.set_header('Expires', '0')
    return response

def retension_thread():
    previous_check_time = 0
    while not STOP_THREADS:
        now = time.time()
        if now - previous_check_time > 10 * 60:
            log('Check for outdated files')
            check_retention()
            previous_check_time = now
        time.sleep(2)

if __name__ == '__main__':
    log('Loading...')

    # treat more file extensions as test files (so preview in browser will be available)
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

    if not os.path.isdir(STORAGE_DIRECTORY):
        os.makedirs(STORAGE_DIRECTORY, 755)

    thread = threading.Thread(target = retension_thread)
    thread.start()

    log('Start server...')

    bottle.run(app=bottle.app(),
        server=config.WEB_SERVER,
        host=config.LISTEN_HOST,
        port=config.LISTEN_PORT,
        debug=config.IS_DEBUG)

    log('Unloading...')
    STOP_THREADS = True
    thread.join()
    log('Unloaded')
