import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from subprocess import Popen
from tempfile import TemporaryDirectory
from typing import Optional, Sequence, List

import requests
from dataclasses_json import dataclass_json  # type: ignore
from requests import Response

from utils.testing_helpers import get_random_bytes, wait_net_service

LOGGER = logging.getLogger('speed_test')

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 35080


@dataclass
class RunningServer:
    temp_directory: 'TemporaryDirectory[str]'
    process: 'Popen[bytes]'


@dataclass_json
@dataclass
class FileOnServer:
    url: str
    url_filename: str
    display_filename: str
    size: int
    modified: int


class SpeedTest:

    def __init__(self) -> None:
        self._base_url: Optional[str] = None

    @staticmethod
    def run_child_server(server_name: str, port: int) -> RunningServer:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.join(script_dir, '..')
        server_py = os.path.join(root_dir, 'server.py')

        temp_directory = TemporaryDirectory()
        LOGGER.info('created temporary directory: %s', temp_directory.name)

        subenv = os.environ.copy()
        subenv['LIMBO_WEB_SERVER'] = server_name
        subenv['LIMBO_LISTEN_HOST'] = LISTEN_HOST
        subenv['LIMBO_LISTEN_PORT'] = str(port)
        subenv['LIMBO_STORAGE_DIRECTORY'] = temp_directory.name
        # don't waste time for saving files:
        subenv['LIMBO_DISABLE_STORAGE'] = '0'

        process = Popen([sys.executable, server_py], cwd=root_dir, env=subenv)
        try:
            wait_net_service(LISTEN_HOST, port, 10)
        except Exception as exc:
            LOGGER.exception('Got exception: %s', repr(exc))
            process.terminate()
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
        LOGGER.info('Request: GET %s', url)
        response = requests.get(url)
        self.check_response(response)
        files: List[FileOnServer] =\
            FileOnServer.schema().load(response.json(), many=True)  # type: ignore  # pylint: disable=no-member
        files = sorted(files, key=lambda item: item.display_filename)
        return files

    def upload_file(self, original_filename: str, filedata: bytes) -> None:
        assert self._base_url is not None
        url = self._base_url + '/cgi/upload/'
        LOGGER.info('Request: POST %s', url)

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

    def do_all_tests(self, server_name: str) -> None:
        port = LISTEN_PORT

        self._base_url = 'http://' + LISTEN_HOST + ':' + str(port)
        LOGGER.info('DoTest("%s") start', server_name)
        server: RunningServer = self.run_child_server(server_name, port)

        with server.temp_directory:
            try:
                self.get_stored_files()

                data = get_random_bytes(800123123, 42)

                LOGGER.info('===============================================')
                time1 = datetime.now()
                self.upload_file('some_file.dat', data)
                time2 = datetime.now()
                LOGGER.info('===============================================')
                mib = 1024 * 1024
                seconds = (time2 - time1).total_seconds()
                bandwidth_mib = len(data) / seconds / mib
                LOGGER.info('Data size: %.3f MiB', len(data) / mib)
                LOGGER.info('Time taken: %.3f sec', seconds)
                LOGGER.info('Bandwidth: %.3f MiB/s', bandwidth_mib)
                LOGGER.info('===============================================')

            finally:
                server.process.terminate()

        LOGGER.info('DoAllTests("%s") finished', server_name)


def main() -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    server_name = sys.argv[1] if len(sys.argv) > 1 else 'cherrypy'
    LOGGER.info('Speed testing %s...', server_name)
    test = SpeedTest()
    test.do_all_tests(server_name)


if __name__ == '__main__':
    main()
