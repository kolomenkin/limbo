#!/usr/bin/python3

from datetime import datetime
from numpy import random
from os import path as os_path, environ as os_environ
from requests import get as requests_get, post as requests_post
from subprocess import Popen as subprocess_Popen
from sys import argv as sys_argv
from tempfile import TemporaryDirectory
from time import strftime as time_strftime

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 35080


def log(*args):
    print('SPD>', time_strftime('%Y-%m-%d %H:%M:%S:'), *args)


def get_random_bytes(size, seed):
    random.seed(seed)
    return random.bytes(size)


class SpeedTest:

    def __init__(self):
        self._base_url = None

    def RunServer(self, server_name, port):
        script_dir = os_path.dirname(os_path.abspath(__file__))
        root_dir = os_path.join(script_dir, '..')
        server_py = os_path.join(root_dir, 'server.py')

        tmpdirname = TemporaryDirectory()
        log('created temporary directory: ' + tmpdirname.name)

        subenv = os_environ.copy()
        subenv['LIMBO_WEB_SERVER'] = server_name
        subenv['LIMBO_LISTEN_HOST'] = LISTEN_HOST
        subenv['LIMBO_LISTEN_PORT'] = str(port)
        subenv['LIMBO_STORAGE_DIRECTORY'] = tmpdirname.name
        # don't waste time for saving files:
        subenv['LIMBO_DISABLE_STORAGE'] = '1'

        pid = subprocess_Popen(['python', server_py], cwd=root_dir, env=subenv)
        return [tmpdirname, pid]

    def CheckHttpError(self, r):
        if r.status_code != 200:
            raise ValueError('Bad server reply code: ' + str(r.status_code))

    def GetStoredFiles(self):
        url = self._base_url + '/cgi/enumerate/'
        log('Request: GET ' + url)
        r = requests_get(url)
        self.CheckHttpError(r)
        files = r.json()
        files = sorted(files, key=lambda item: item['display_filename'])
        return files

    def UploadFile(self, original_filename, filedata):
        url = self._base_url + '/cgi/upload/'
        log('Request: POST ' + url)

        # files = {'file': (original_filename, filedata)}
        # r = requests_post(url, files=files)
        # NOTE: requests library has bad support for
        #       upload files with utf-8 names
        # It encodes utf-8 file name in the following form:
        # filename*=utf-8\'\'%D1%80%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9.%D1%84%D0%B0%D0%B9%D0%BB
        # This is why I'm constructing multipart message manually

        boundary = b'Ab522e64be24449aa3131245da23b3yZ'
        encoded_filename = original_filename.encode('utf-8')
        payload = b'--' + boundary + b'\r\nContent-Disposition: form-data' \
            + b'; name="file"; filename="' + encoded_filename \
            + b'"\r\n\r\n' + filedata + b'\r\n--' + boundary + b'--\r\n'

        content_type = 'multipart/form-data; boundary=' \
            + boundary.decode('utf-8')
        headers = {'Content-Type': content_type}

        r = requests_post(url, data=payload, headers=headers)

        self.CheckHttpError(r)

    def DoAllTests(self, server_name):
        global LISTEN_PORT
        port = LISTEN_PORT
        self._server_name = server_name
        self._base_url = 'http://' + LISTEN_HOST + ':' + str(port)
        log('DoTest("' + self._server_name + '") start')
        tmpdirname, pid = self.RunServer(self._server_name, port)

        with tmpdirname:
            try:
                self.GetStoredFiles()

                data = get_random_bytes(800123123, 42)

                log('===============================================')
                time1 = datetime.now()
                self.UploadFile('some_file.dat', data)
                time2 = datetime.now()
                log('===============================================')
                MB = 1024 * 1024
                seconds = (time2 - time1).total_seconds()
                bandwidth_mb = len(data) / seconds / MB
                log('Data size: %.3f MB' % (len(data) / MB))
                log('Time taken: %.3f sec' % (seconds))
                log('Bandwidth: %.3f MB/s' % (bandwidth_mb))
                log('===============================================')

            finally:
                pid.terminate()

        tmpdirname = None
        log('DoAllTests("' + self._server_name + '") finished')


if __name__ == '__main__':
    server_name = sys_argv[1] if len(sys_argv) > 1 else 'cherrypy'
    log('Speed testing ' + server_name + '...')
    test = SpeedTest()
    test.DoAllTests(server_name)
