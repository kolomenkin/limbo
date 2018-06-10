from base64 import b64decode
from numpy import random
from os import path as os_path
import tempfile
from unittest import TestCase

# add parent dir to search for imported modules
# import os, sys
# myPath = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, myPath + '/../')
from lib_file_storage import FileStorage


def get_random_bytes(size, seed):
    random.seed(seed)
    return random.bytes(size)


def GetFileStorage():
    tmpdirname = tempfile.TemporaryDirectory()
    print('created temporary directory', tmpdirname)
    storage = FileStorage(tmpdirname.name, 24 * 3600)
    return [tmpdirname, storage]


class FileStorageTestCase(TestCase):

    def process_single_file(self, original_filename, original_filedata):
        tmpdirname, storage = GetFileStorage()

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_to_write(original_filename) as file:
            if len(original_filedata) > 0:
                file.write(original_filedata)

        files = storage.enumerate_files()

        self.assertEqual(1, len(files))
        item = files[0]
        url_filename = item['url_filename']
        display_filename = item['display_filename']
        self.assertEqual(display_filename, original_filename)
        size = os_path.getsize(item['full_disk_filename'])
        self.assertEqual(size, len(original_filedata))

        storage_directory, disk_filename, display_filename2 = \
            storage.get_file_info_to_read(url_filename)
        self.assertEqual(storage_directory, tmpdirname.name)
        self.assertEqual(display_filename2, display_filename)

        fullpath = os_path.join(storage_directory, disk_filename)
        with open(fullpath, 'rb') as file:
            filedata = file.read()
            self.assertEqual(filedata, original_filedata)

        storage.remove_file(url_filename)

        self.assertEqual(0, len(storage.enumerate_files()))

    def test_basic_text1(self):
        self.process_single_file('file.txt', b'')

    def test_basic_text2(self):
        self.process_single_file('file.txt', b'A')

    def test_basic_text3(self):
        self.process_single_file('file.txt', b'abcde')

    def test_big_file(self):
        self.process_single_file('file.dat', get_random_bytes(1234567, 42))

    def test_binary_data(self):
        # data (hex): 00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF
        data = b64decode('ABEiM0RVZneImaq7zN3u/w==')
        self.process_single_file('file.dat', data)

    def test_utf8_filename(self):
        # russian is used in file name
        # filename: русский.файл
        #      hex: D1 80 D1 83 D1 81 D1 81 D0 BA D0 B8
        #           D0 B9 2E D1 84 D0 B0 D0 B9 D0 BB
        filename = b64decode('0YDRg9GB0YHQutC40Lku0YTQsNC50Ls=')
        filename = filename.decode('utf-8')
        self.process_single_file(filename, b'Z')

    def test_multiple_files(self):
        tmpdirname, storage = GetFileStorage()

        original_filename1 = 'file1.zip'
        original_filedata1 = b'abcde'
        original_filename2 = 'file2.doc'
        original_filedata2 = b'The quick brown fox jumped over the lazy dog'

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_to_write(original_filename1) as file:
            file.write(original_filedata1)

        self.assertEqual(1, len(storage.enumerate_files()))

        with storage.open_file_to_write(original_filename2) as file:
            file.write(original_filedata2)

        files = storage.enumerate_files()
        self.assertEqual(2, len(files))

        files = sorted(files, key=lambda item: item['display_filename'])

        item = files[0]
        url_filename1 = item['url_filename']
        self.assertEqual(item['display_filename'], original_filename1)
        size = os_path.getsize(item['full_disk_filename'])
        self.assertEqual(size, len(original_filedata1))

        item = files[1]
        url_filename2 = item['url_filename']
        self.assertEqual(item['display_filename'], original_filename2)
        size = os_path.getsize(item['full_disk_filename'])
        self.assertEqual(size, len(original_filedata2))

        storage.remove_file(url_filename1)

        self.assertEqual(1, len(storage.enumerate_files()))

        storage.remove_file(url_filename2)

        self.assertEqual(0, len(storage.enumerate_files()))

    def test_remove_all_files(self):
        tmpdirname, storage = GetFileStorage()

        self.assertEqual(0, len(storage.enumerate_files()))

        with storage.open_file_to_write('file1') as file:
            file.write(b'')

        with storage.open_file_to_write('file2') as file:
            file.write(b'AAA')

        with storage.open_file_to_write('file3') as file:
            file.write(b'bbbbb')

        self.assertEqual(3, len(storage.enumerate_files()))

        storage.remove_all_files()

        self.assertEqual(0, len(storage.enumerate_files()))

    def test_start_stop(self):
        tmpdirname, storage = GetFileStorage()
        storage.start()
        storage.stop()
