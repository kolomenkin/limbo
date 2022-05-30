from base64 import b64decode
from dataclasses import dataclass
from os import path as os_path
from tempfile import TemporaryDirectory
from typing import Sequence
from unittest import TestCase

from numpy import random

# add parent dir to search for imported modules
# import os, sys
# script_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, script_dir + '/../')
from lib_file_storage import DisplayFileItem, FileStorage, StorageFileItem


def get_random_bytes(size: int, seed: int) -> bytes:
    random.seed(seed)
    result = random.bytes(size)
    assert isinstance(result, bytes)
    return result


@dataclass
class TempStorage:
    temp_directory: 'TemporaryDirectory[str]'
    storage: FileStorage


def get_temp_file_storage() -> TempStorage:
    temp_directory = TemporaryDirectory()  # pylint: disable=consider-using-with
    print('created temporary directory: ' + temp_directory.name)
    storage = FileStorage(temp_directory.name, 24 * 3600)
    return TempStorage(temp_directory=temp_directory, storage=storage)


class FileStorageTestCase(TestCase):

    def process_single_file(self, original_filename: str, original_filedata: bytes) -> None:
        temp_storage = get_temp_file_storage()
        storage = temp_storage.storage

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_writer(original_filename) as writer:
            if len(original_filedata) > 0:
                writer.write(original_filedata)

        files: Sequence[DisplayFileItem] = storage.enumerate_files()

        self.assertEqual(1, len(files))
        item = files[0]
        url_filename = item.url_filename
        display_filename = item.display_filename
        self.assertEqual(display_filename, original_filename)
        size = os_path.getsize(item.full_disk_filename)
        self.assertEqual(size, len(original_filedata))

        info: StorageFileItem = storage.get_file_info_to_read(url_filename)
        self.assertEqual(info.storage_directory, temp_storage.temp_directory.name)
        self.assertEqual(info.display_filename, display_filename)

        fullpath = os_path.join(info.storage_directory, info.disk_filename)
        with open(fullpath, 'rb') as file:
            filedata = file.read()
            self.assertEqual(filedata, original_filedata)

        storage.remove_file(url_filename)

        self.assertEqual(0, len(storage.enumerate_files()))

    def test_basic_text1(self) -> None:
        self.process_single_file('file.txt', b'')

    def test_basic_text2(self) -> None:
        self.process_single_file('file.txt', b'A')

    def test_basic_text3(self) -> None:
        self.process_single_file('file.txt', b'abcde')

    def test_big_file(self) -> None:
        self.process_single_file('file.dat', get_random_bytes(1234567, 42))

    def test_binary_data(self) -> None:
        # data (hex): 00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF
        data = b64decode('ABEiM0RVZneImaq7zN3u/w==')
        self.process_single_file('file.dat', data)

    def test_utf8_filename(self) -> None:
        # russian is used in file name
        # filename: русский.файл
        #      hex: D1 80 D1 83 D1 81 D1 81 D0 BA D0 B8
        #           D0 B9 2E D1 84 D0 B0 D0 B9 D0 BB
        filename_bytes = b64decode('0YDRg9GB0YHQutC40Lku0YTQsNC50Ls=')
        filename = filename_bytes.decode('utf-8')
        self.process_single_file(filename, b'Z')

    def test_multiple_files(self) -> None:
        temp_storage = get_temp_file_storage()
        storage = temp_storage.storage

        original_filename1 = 'file1.zip'
        original_filedata1 = b'abcde'
        original_filename2 = 'file2.doc'
        original_filedata2 = b'The quick brown fox jumped over the lazy dog'

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_writer(original_filename1) as writer:
            writer.write(original_filedata1)

        self.assertEqual(1, len(storage.enumerate_files()))

        with storage.open_file_writer(original_filename2) as writer:
            writer.write(original_filedata2)

        files: Sequence[DisplayFileItem] = storage.enumerate_files()
        self.assertEqual(2, len(files))

        files = sorted(files, key=lambda item: item.display_filename)

        item = files[0]
        url_filename1 = item.url_filename
        self.assertEqual(item.display_filename, original_filename1)
        size = os_path.getsize(item.full_disk_filename)
        self.assertEqual(size, len(original_filedata1))

        item = files[1]
        url_filename2 = item.url_filename
        self.assertEqual(item.display_filename, original_filename2)
        size = os_path.getsize(item.full_disk_filename)
        self.assertEqual(size, len(original_filedata2))

        storage.remove_file(url_filename1)

        self.assertEqual(1, len(storage.enumerate_files()))

        storage.remove_file(url_filename2)

        self.assertEqual(0, len(storage.enumerate_files()))

    def test_remove_all_files(self) -> None:
        temp_storage = get_temp_file_storage()
        storage = temp_storage.storage

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_writer('file1') as writer:
            writer.write(b'')

        with storage.open_file_writer('file2') as writer:
            writer.write(b'AAA')

        with storage.open_file_writer('file3') as writer:
            writer.write(b'bbbbb')

        self.assertEqual(3, len(storage.enumerate_files()))

        storage.remove_all_files()

        self.assertEqual(0, len(storage.enumerate_files()))

    @staticmethod
    def test_start_stop() -> None:
        temp_storage = get_temp_file_storage()
        storage = temp_storage.storage

        storage.start()
        storage.stop()
