import config

import bottle
import io
import os
import random
import re
import stat
import sys
import time

bottle.TEMPLATE_PATH = ['./static/templates']
StorageDirectory = os.path.abspath(config.STORAGE_DIRECTORY)
FilesSubdir = '/files/'

def size_format(b):
    if b < 10000:
        return '%i' % b + ' B'
    elif 10000 <= b < 10000000:
        return '%.1f' % float(b/1000) + ' KB'
    elif 10000000 <= b < 10000000000:
        return '%.1f' % float(b/1000000) + ' MB'
    elif 10000000000 <= b < 10000000000000:
        return '%.1f' % float(b/1000000000) + ' GB'
    elif 10000000000000 <= b:
        return '%.1f' % float(b/1000000000000) + ' TB'

def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]        

def clean_filename(filename):
    s = re.sub('[\\\\:\'\[\]/",<>&^$+*?;]', '_', filename)
    s = re.sub('^(CON|PRN|AUX|NUL|COM\d|LPT\d)$', 'SPECIAL', s, flags=re.IGNORECASE)
    return s

def check_retention():
    for file in os.listdir(StorageDirectory):
        fullname = os.path.join(StorageDirectory, file)
        if os.path.isfile(fullname):
            if file_age_in_seconds(fullname) > config.MAX_STORAGE_SECONDS:
                print("DBG> Remove too old file: " + fullname)
                os.remove(fullname)

@bottle.route('/')
@bottle.view('homepage.html')
def homepage():
    check_retention()
    files = []
    for file in os.listdir(StorageDirectory):
        fullname = os.path.join(StorageDirectory, file)
        if os.path.isfile(fullname):
            files.append(
            {
                'name': file,
                'url': FilesSubdir + file,
                'size': size_format(os.path.getsize(fullname)),
            })
    return {
            'title': 'Duplo: file sharing web page',
            'h1': 'Duplo, file sharing web page',
            'rnd': random.randint(1, 100),
            'files': files,
        }

@bottle.post('/cgi/shareText/')
def cgi_shareText():
    check_retention()
    title = bottle.request.forms.title
    body = bottle.request.forms.body
    fullname = os.path.join(StorageDirectory, clean_filename(title) + '.txt')
    print("DBG> Share text into: " + fullname)
    with io.open(fullname, 'w', encoding='utf-8') as file:
        file.write(body)
    return 'OK'

@bottle.post('/cgi/upload/')
def cgi_upload():
    check_retention()
    upload = bottle.request.files.get('file')
    fullname = os.path.join(StorageDirectory, clean_filename(upload.filename))
    print("DBG> Upload file: " + fullname)
    upload.save(fullname)
    return 'OK'

@bottle.post('/cgi/remove/')
def cgi_remove():
    check_retention()
    file = bottle.request.forms.fileName
    fullname = os.path.join(StorageDirectory, clean_filename(file))
    print("DBG> Remove file: " + fullname)
    os.remove(fullname)
    return 'OK'

@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    root_folder = os.path.abspath(os.path.dirname(__file__))
    return bottle.static_file(filepath, root=os.path.join(root_folder, 'static'))

@bottle.route(FilesSubdir + '<filepath:path>')
def server_storage(filepath):
    return bottle.static_file(filepath, root=StorageDirectory)

if __name__ == '__main__':
    print('Loading...')
    if not os.path.isdir(StorageDirectory):
        os.makedirs(StorageDirectory, 744)
    bottle.run(app=bottle.app(), server='wsgiref', host=config.LISTEN_IP, port=config.LISTEN_PORT, threaded=True)
