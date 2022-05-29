import os
import subprocess
import sys
from base64 import b64decode
from dataclasses import dataclass
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Any, List, Optional, Sequence
from unittest import TestCase
from urllib.parse import urlparse

import requests
from dataclasses_json import dataclass_json, Undefined
from requests import Response

from utils.testing_helpers import get_random_bytes, get_random_text, wait_net_service


DEFAULT_LISTEN_HOST = '127.0.0.1'
DEFAULT_LISTEN_PORT = 35080


def log(*args: Any) -> None:
    # %(asctime)s000 - %(process)5d - %(name)s - %(levelname)s - %(message)s
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'), f'- {os.getpid(): >5} - tst - INFO -', *args)


@dataclass
class RunningServer:
    temp_directory: 'TemporaryDirectory[str]'
    process: 'subprocess.Popen[bytes]'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FileOnServer:
    url: str
    url_filename: str
    display_filename: str
    size: int


class ServerTestCase(TestCase):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(ServerTestCase, self).__init__(*args, **kwargs)
        # added to uploaded to server text fragment names:
        self._text_filename_postfix = '.txt'
        self._server_name: Optional[str] = None
        self._base_url: Optional[str] = None

    @staticmethod
    def run_child_server(server_name: str, host: str, port: int) -> RunningServer:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.join(script_dir, '..')
        server_py = os.path.join(root_dir, 'server.py')

        temp_directory = TemporaryDirectory()
        log('created temporary directory: ' + temp_directory.name)

        subenv = os.environ.copy()
        subenv['LIMBO_WEB_SERVER'] = server_name
        subenv['LIMBO_LISTEN_HOST'] = host
        subenv['LIMBO_LISTEN_PORT'] = str(port)
        subenv['LIMBO_STORAGE_DIRECTORY'] = temp_directory.name
        subenv['LIMBO_IS_DEBUG'] = '1'
        subenv['PYTHONUNBUFFERED'] = '1'

        log(f'Run subprocess: {sys.executable} {server_py}')
        log(f'Subprocess server name: {server_name}')
        log(f'Subprocess listen port: {port}')

        process = subprocess.Popen(
            args=[sys.executable, server_py],
            stderr=subprocess.STDOUT,
            cwd=root_dir,
            env=subenv,
        )

        log(f'Subprocess PID: {process.pid}')

        try:
            started_ok = wait_net_service(host, port, 5)
            if started_ok:
                log('Server ' + server_name + ' started OK')
            else:
                log('Server ' + server_name + ' failed to start')
                raise RuntimeError('Server failed to start')
        except Exception as exc:
            log('Got exception: ', repr(exc))
            log(f'Terminate subprocess with {server_name} server...')
            process.terminate()
            log(f'Wait subprocess with {server_name} server (PID {process.pid})...')
            process.wait()
            log(f'Subprocess with {server_name} server finished')
            temp_directory.cleanup()
            raise
        return RunningServer(temp_directory=temp_directory, process=process)

    @staticmethod
    def check_response(response: Response) -> None:
        if response.status_code != 200:
            raise Exception('Bad server reply code: ' + str(response.status_code))

    def get_stored_files(self) -> Sequence[FileOnServer]:
        assert self._base_url is not None
        url = self._base_url + '/cgi/enumerate/'
        log('Request: GET ' + url)
        response = requests.get(url)
        self.check_response(response)
        files: List[FileOnServer] = \
            FileOnServer.schema().load(response.json(), many=True)  # type: ignore  # pylint: disable=no-member
        files = sorted(files, key=lambda item: item.display_filename)
        return files

    def download_file(self, url_path: str) -> bytes:
        assert self._base_url is not None
        url = self._base_url + url_path
        log('Request: GET ' + url)
        response = requests.get(url)
        self.check_response(response)
        return response.content or b''

    def upload_file(self, original_filename: str, filedata: bytes) -> None:
        assert self._base_url is not None
        url = self._base_url + '/cgi/upload/'
        log('Request: POST ' + url)

        # files = {'file': (original_filename, filedata)}
        # r = requests.post(url, files=files)
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

        content_type = 'multipart/form-data; boundary=' + boundary.decode('utf-8')
        headers = {'Content-Type': content_type}

        response = requests.post(url, data=payload, headers=headers)

        self.check_response(response)

    def upload_text(self, title: str, text: str) -> None:
        assert self._base_url is not None
        url = self._base_url + '/cgi/addtext/'
        log('Request: POST ' + url)
        formdata = {'title': title, 'body': text}
        response = requests.post(url, data=formdata)
        self.check_response(response)

    def remove_file(self, url_filename: str) -> None:
        assert self._base_url is not None
        url = self._base_url + '/cgi/remove/'
        log('Request: POST ' + url)
        formdata = {'fileName': url_filename}
        response = requests.post(url, data=formdata)
        self.check_response(response)

    def remove_all_files(self) -> None:
        assert self._base_url is not None
        url = self._base_url + '/cgi/remove-all/'
        log('Request: POST ' + url)
        response = requests.post(url, data='')
        self.check_response(response)

    def on_test_start(self, test_name: str) -> None:
        assert self._server_name is not None
        log('=============================================')
        log('TEST: ' + self._server_name + ': ' + test_name)
        log('=============================================')

    def do_test_upload_file(self, name: str, data: bytes) -> None:
        self.on_test_start('FileUpload("' + name + '")')
        self.remove_all_files()
        self.assertEqual(0, len(self.get_stored_files()))

        self.upload_file(name, data)
        files = self.get_stored_files()
        self.assertEqual(1, len(files))
        log('File URL: ' + files[0].url)
        self.assertEqual(name, files[0].display_filename)
        self.assertEqual(len(data), files[0].size)
        url_filename = files[0].url_filename
        data2 = self.download_file(files[0].url)
        self.assertEqual(data2, data)
        self.remove_file(url_filename)
        self.assertEqual(0, len(self.get_stored_files()))

    def do_test_upload_text(self, name: str, text: str) -> None:
        self.on_test_start('TextUpload("' + name + '")')
        self.remove_all_files()
        self.assertEqual(0, len(self.get_stored_files()))

        self.upload_text(name, text)
        files = self.get_stored_files()
        self.assertEqual(1, len(files))
        log('File URL: ' + files[0].url)
        self.assertEqual(name + self._text_filename_postfix, files[0].display_filename)
        self.assertEqual(len(text), files[0].size)
        data2 = self.download_file(files[0].url)
        self.assertEqual(data2, text.encode('utf-8'))
        url_filename = files[0].url_filename
        self.remove_file(url_filename)
        self.assertEqual(0, len(self.get_stored_files()))

    def do_test_few_files(self) -> None:
        self.on_test_start('FewFiles')
        self.remove_all_files()
        self.assertEqual(0, len(self.get_stored_files()))

        self.upload_text('data_A', 'aaa')
        self.upload_text('data_B', 'bbb')
        self.upload_file('file1.zip', b'abcd')
        self.upload_file('file2.txt', b'ABCD')
        files = self.get_stored_files()
        self.assertEqual(4, len(files))
        log('File URL: ' + files[0].url)
        log('File URL: ' + files[1].url)
        log('File URL: ' + files[2].url)
        log('File URL: ' + files[3].url)
        self.assertEqual('data_A' + self._text_filename_postfix, files[0].display_filename)
        self.assertEqual('data_B' + self._text_filename_postfix, files[1].display_filename)
        self.assertEqual('file1.zip', files[2].display_filename)
        self.assertEqual('file2.txt', files[3].display_filename)
        self.remove_all_files()
        self.assertEqual(0, len(self.get_stored_files()))

    def do_all_tests(self, server_name: str, base_url: str) -> None:
        self._server_name = server_name
        self._base_url = base_url.rstrip('/')

        files = self.get_stored_files()
        self.assertEqual(0, len(files))

        self.do_test_upload_text('a', '')
        self.do_test_upload_text('file.txt', 'abcdef')
        text = get_random_text(90000, 42)
        self.do_test_upload_text('some_file.dat', text)

        self.do_test_upload_file('a', b'')
        self.do_test_upload_file('file.txt', b'abcdef')
        data = get_random_bytes(1234567, 42)
        self.do_test_upload_file('some_file.dat', data)

        # russian is used in file name
        # filename: русский.файл
        #      hex: D1 80 D1 83 D1 81 D1 81 D0 BA D0 B8
        #           D0 B9 2E D1 84 D0 B0 D0 B9 D0 BB
        filename_bytes = b64decode('0YDRg9GB0YHQutC40Lku0YTQsNC50Ls=')
        filename = filename_bytes.decode('utf-8')
        # Paste server is known as not supporting utf-8 in file names
        if server_name != 'paste':
            self.do_test_upload_file(filename, b'some text')

        self.do_test_few_files()

        self.remove_all_files()
        self.assertEqual(0, len(self.get_stored_files()))

    def run_server_and_do_all_tests(self, server_name: str) -> None:
        host = DEFAULT_LISTEN_HOST
        port = DEFAULT_LISTEN_PORT
        base_url = 'http://' + host + ':' + str(port)
        log('RunServerAndDoAllTests("' + server_name + '") start')
        server: RunningServer = self.run_child_server(server_name, host, port)

        with server.temp_directory:
            try:
                self.do_all_tests(server_name, base_url)
            finally:
                log(f'Terminate subprocess with {server_name} server')
                server.process.terminate()
                log(f'Wait subprocess with {server_name} server (PID {server.process.pid})...')
                server.process.wait()
                log(f'Subprocess with {server_name} server finished')

        log('RunServerAndDoAllTests("' + server_name + '") finished')

    def test_cherrypy(self) -> None:
        self.run_server_and_do_all_tests('cherrypy')

    # def test_flup(self) -> None:
    #     self.RunServerAndDoAllTests('flup')
    #
    # def test_gevent(self) -> None:
    #     self.RunServerAndDoAllTests('gevent')
    #
    # def test_gunicorn(self) -> None:
    #     self.RunServerAndDoAllTests('gunicorn')

    # Paste server is known as not supporting utf-8 in file names
    def test_paste(self) -> None:
        self.run_server_and_do_all_tests('paste')

    def test_tornado(self) -> None:
        self.run_server_and_do_all_tests('tornado')

    def test_twisted(self) -> None:
        self.run_server_and_do_all_tests('twisted')

    def test_waitress(self) -> None:
        self.run_server_and_do_all_tests('waitress')

    # def test_wsgiref(self) -> None:
    #     self.RunServerAndDoAllTests('wsgiref')


def main() -> None:
    server_name = sys.argv[1] if len(sys.argv) > 1 else 'cherrypy'

    log('Begin testing ' + server_name + '...')
    test = ServerTestCase()
    if server_name.startswith('http://') or server_name.startswith('https://'):
        log('Testing external server: ' + server_name)

        # Waiting for external service is not necessary since we have external waiting in CI
        # using Docker image kolomenkin/wait-for-it
        # And external waiting may work more correct if external service is running inside of Docker
        # while test code is running on host.
        url = urlparse(server_name)
        assert url.hostname is not None
        assert url.port is not None
        started_ok = wait_net_service(url.hostname, url.port, 5)
        if started_ok:
            log('Server ' + server_name + ' started OK')
        else:
            log('Server ' + server_name + ' failed to start')
            sys.exit(1)

        test.do_all_tests('external', server_name)
    else:
        log('Testing internal server: ' + server_name)
        test.run_server_and_do_all_tests(server_name)


if __name__ == '__main__':
    main()
