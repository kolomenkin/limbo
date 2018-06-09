#!/usr/bin/python3
# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)

from lib_common import log, file_age_in_seconds

import io
import os
import re
import threading
import time


def clean_filename(filename):
    s = filename
    # https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words
    # limit max length:
    s = s[:250]
    # dots and space at end of file name are ignored:
    s = s.rstrip('. ')
    # replace forbidden symbols:
    s = re.sub('[\\\\:\'\\[\\]/",<>&^$+*?;|\x00-\x1F]', '_', s)
    # Deny special file names:
    # This is important not to make string longer here!
    s = re.sub('^(CON|PRN|AUX|NUL|COM\\d|LPT\\d)($|\..*)', 'DEV\\2',
               s, flags=re.IGNORECASE)
    s = 'EMPTY' if s == '' else s
    return s


class FileStorage:
    def __init__(self, storage_directory, max_store_time_seconds):
        log('FileStorage: create')
        self._storage_directory = os.path.abspath(storage_directory)
        self._max_store_time_seconds = max_store_time_seconds
        self._retension_thread = None
        self._stopping = False

        if not os.path.isdir(self._storage_directory):
            os.makedirs(self._storage_directory, 755)

    def start(self):
        log('FileStorage: start')
        self._retension_thread = \
            threading.Thread(target=self._retension_thread_procedure)
        self._retension_thread.start()

    def stop(self):
        log('FileStorage: stop')
        self._stopping = True
        self._retension_thread.join()

    def enumerate_files(self):
        files = []
        for file in os.listdir(self._storage_directory):
            fullname = os.path.join(self._storage_directory, file)
            if os.path.isfile(fullname):
                files.append(
                    {
                        'fulldiskname': fullname,
                        'urlname': file,
                        'displayname': file,
                    })
        return files

    def open_file_to_write(self, filename):
        fullname = os.path.join(self._storage_directory,
                                FileStorage._canonize_file(filename))
        log('FileStorage: Upload file: ' + fullname)
        return io.open(fullname, 'xb')

    def get_file_info_to_read(self, filename):
        return [self._storage_directory, FileStorage._canonize_file(filename)]

    def remove_file(self, filename):
        fullname = os.path.join(self._storage_directory,
                                FileStorage._canonize_file(filename))
        log('FileStorage: Remove file: "' + fullname + '"; size: ' + str(os.path.getsize(fullname)))
        os.remove(fullname)

    def _canonize_file(filename):
        canonizeed = clean_filename(filename)
        if clean_filename(canonizeed) != canonizeed:
            raise Exception('clean_filename failed to canonize file name',
                            filename)
        return canonizeed

    def _retension_thread_procedure(self):
        log('FileStorage: Retension thread started')
        previous_check_time = 0
        while not self._stopping:
            now = time.time()
            if now - previous_check_time > 10 * 60:  # every 10 minutes
                log('FileStorage: Check for outdated files')
                self._check_retention()
                previous_check_time = now
            time.sleep(2)

    def _check_retention(self):
        for file in os.listdir(self._storage_directory):
            fullname = os.path.join(self._storage_directory, file)
            if os.path.isfile(fullname):
                age = file_age_in_seconds(fullname)
                if age > self._max_store_time_seconds:
                    log('FileStorage: Remove outdated file: ' + fullname)
                    os.remove(fullname)
