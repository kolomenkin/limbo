import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Sequence

import requests
from dataclasses_json import dataclass_json
from requests import Response

from utils.testing_helpers import get_random_bytes, wait_net_service


LOGGER = logging.getLogger('speed_test')

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 35080


@dataclass
class RunningServer:
    temp_directory: 'TemporaryDirectory[str]'
    process: 'subprocess.Popen[bytes]'


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
        script_dir = Path(__file__).parent.absolute()
        root_dir = script_dir.parent
        server_py = root_dir / 'server.py'

        temp_directory = TemporaryDirectory()  # pylint: disable=consider-using-with
        LOGGER.info('created temporary directory: %s', temp_directory.name)

        subenv = os.environ.copy()
        subenv['LIMBO_WEB_SERVER'] = server_name
        subenv['LIMBO_LISTEN_HOST'] = LISTEN_HOST
        subenv['LIMBO_LISTEN_PORT'] = str(port)
        subenv['LIMBO_STORAGE_DIRECTORY'] = temp_directory.name
        # don't waste time for saving files:
        subenv['LIMBO_DISABLE_STORAGE'] = '0'

        LOGGER.info('Run subprocess: %s %s', sys.executable, server_py)
        LOGGER.info('Subprocess server name: %s', server_name)
        LOGGER.info('Subprocess listen port: %d', port)

        process = subprocess.Popen(  # pylint: disable=consider-using-with
            args=[sys.executable, str(server_py)],
            cwd=root_dir,
            env=subenv,
        )

        LOGGER.info('Subprocess PID: %d', process.pid)

        try:
            started_ok = wait_net_service(LISTEN_HOST, port, 5)
            if started_ok:
                LOGGER.info('Server %s started OK', server_name)
            else:
                LOGGER.error('Server %s failed to start', server_name)
                raise RuntimeError('Server failed to start')
        except Exception as exc:
            LOGGER.exception('Got exception: %s', repr(exc))
            LOGGER.info('Terminate subprocess with %s server...', server_name)
            process.terminate()
            LOGGER.info('Wait subprocess with %s server (PID %d)...', server_name, process.pid)
            process.wait()
            LOGGER.info('Subprocess with %s server finished', server_name)
            temp_directory.cleanup()
            raise

        return RunningServer(temp_directory=temp_directory, process=process)

    @staticmethod
    def check_response(response: Response) -> None:
        if response.status_code != 200:
            raise Exception(f'Bad server reply code: {response.status_code}')

    def get_stored_files(self) -> Sequence[FileOnServer]:
        assert self._base_url is not None
        url = self._base_url + '/cgi/enumerate/'
        LOGGER.info('Request: GET %s', url)
        response = requests.get(url)
        self.check_response(response)
        files: List[FileOnServer] = FileOnServer.schema().load(response.json(), many=True)  # type: ignore  # pylint: disable=no-member  # noqa: E501
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

        boundary = 'Ab522e64be24449aa3131245da23b3yZ'

        payload_prefix = \
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{original_filename}"\r\n\r\n'
        payload_postfix = f'\r\n--{boundary}--\r\n'
        payload = payload_prefix.encode('utf-8') + filedata + payload_postfix.encode('utf-8')

        headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}

        response = requests.post(url, data=payload, headers=headers)

        self.check_response(response)

    def do_all_tests(self, server_name: str) -> None:
        port = LISTEN_PORT

        self._base_url = f'http://{LISTEN_HOST}:{port}'
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
                LOGGER.info('Terminate subprocess with %s server', server_name)
                server.process.terminate()
                LOGGER.info('Wait subprocess with %s server (PID %d)...', server_name, server.process.pid)
                server.process.wait()
                LOGGER.info('Subprocess with %s server finished', server_name)

        LOGGER.info('DoAllTests("%s") finished', server_name)


def main() -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    server_name = sys.argv[1] if len(sys.argv) > 1 else 'cheroot'
    LOGGER.info('Speed testing %s...', server_name)
    test = SpeedTest()
    test.do_all_tests(server_name)


if __name__ == '__main__':
    main()
