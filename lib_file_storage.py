# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018-2022 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from time import sleep, time
from typing import Any, List, Optional, Sequence
from uuid import uuid4

from lib_common import get_file_modified_unixtime


LOGGER = logging.getLogger('dat')


# ==========================================
# There are 4 types of file names:
# 1) Original file name provided by user
# 2) URL file name for use in URLs
# 3) Disk file name (on server)
# 4) Display name. Used on web page and to save file on end user's computer
# ==========================================


def clean_filename(filename: str) -> str:
    result = filename
    # https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words
    # limit max length:
    result = result[:250]
    # dots and space at end of file name are ignored:
    result = result.rstrip('. ')
    # replace forbidden symbols:
    result = re.sub(r'[\\:\'\[\]/",<>&^$+*?;|\x00-\x1F]', '_', result)
    # Deny special file names:
    # This is important not to make string longer here!
    result = re.sub(r'^(CON|PRN|AUX|NUL|COM\d|LPT\d)($|\..*)', r'DEV\2', result, flags=re.IGNORECASE)
    result = 'EMPTY' if result == '' else result
    return result


class AtomicFile:
    def __init__(self, temp_filename: Path, final_filename: Path):
        if final_filename.is_file():
            raise Exception('Destination file already exists')
        self._temp_filename: Path = temp_filename
        self._final_filename: Path = final_filename
        self._fd = self._temp_filename.open('wb')  # pylint: disable=consider-using-with

    def write(self, data: bytes) -> None:
        self._fd.write(data)

    def close(self) -> None:
        self._fd.close()
        self._temp_filename.rename(self._final_filename)

    def __enter__(self) -> 'AtomicFile':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._fd.close()
        if exc_tb is None:
            # No exception, so rename
            self._temp_filename.rename(self._final_filename)


@dataclass
class DisplayFileItem:
    full_disk_filename: Path
    url_filename: str
    display_filename: str


@dataclass
class StorageFileItem:
    storage_directory: Path
    disk_filename: str
    display_filename: str


class FileStorage:
    def __init__(self, storage_directory: Path, max_store_time_seconds: int):
        LOGGER.info('FileStorage: create("%s", max %d sec)', storage_directory, max_store_time_seconds)
        self._storage_directory: Path = storage_directory.absolute()
        self._temp_directory: Path = self._storage_directory / 'incomplete'
        self._max_store_time_seconds = max_store_time_seconds
        self._retention_thread: Optional[threading.Thread] = None
        self._protect_stop = threading.Lock()
        self._condition_stop = threading.Condition(self._protect_stop)
        self._stopping = False

        self._create_dirs()

    def start(self) -> None:
        LOGGER.info('FileStorage: start')
        self._retention_thread = threading.Thread(target=self._retention_thread_procedure)
        self._retention_thread.start()

    def stop(self) -> None:
        LOGGER.info('FileStorage: stop')
        with self._condition_stop:
            self._stopping = True
            self._condition_stop.notify()
        if self._retention_thread is not None:
            self._retention_thread.join()

    def enumerate_files(self) -> Sequence[DisplayFileItem]:
        if not self._storage_directory.is_dir():
            return []
        files: List[DisplayFileItem] = []
        for disk_filename in self._storage_directory.iterdir():
            if disk_filename.is_file():
                url_filename = self._fname_disk_to_url(disk_filename.name)
                display_filename = self._fname_disk_to_display(disk_filename.name)
                files.append(DisplayFileItem(
                    full_disk_filename=disk_filename,
                    url_filename=url_filename,
                    display_filename=display_filename,
                ))
        return files

    def open_file_writer(self, original_filename: str) -> AtomicFile:
        self._create_dirs()
        disk_filename = self._fname_original_to_disk(original_filename)
        temp_disk_filename = f'{uuid4().hex}.{disk_filename}'
        temp_fullname = self._temp_directory / temp_disk_filename
        fullname = self._storage_directory / disk_filename
        LOGGER.info('FileStorage: Upload file: %s', disk_filename)
        return AtomicFile(temp_fullname, fullname)

    def get_file_info_to_read(self, url_filename: str) -> StorageFileItem:
        disk_filename = self._fname_url_to_disk(url_filename)
        display_filename = self._fname_disk_to_display(disk_filename)
        return StorageFileItem(
            storage_directory=self._storage_directory,
            disk_filename=disk_filename,
            display_filename=display_filename,
        )

    def remove_file(self, url_filename: str) -> None:
        disk_filename = self._fname_url_to_disk(url_filename)
        fullname = self._storage_directory / disk_filename
        file_size = fullname.stat().st_size
        LOGGER.info('FileStorage: Remove file: "%s"; size: %d', disk_filename, file_size)
        fullname.unlink()

    def remove_all_files(self) -> None:
        if not self._storage_directory.is_dir():
            return
        for disk_filename in self._storage_directory.iterdir():
            if disk_filename.is_file():
                file_size = disk_filename.stat().st_size
                LOGGER.info('FileStorage: Remove file: "%s"; size: %d', disk_filename.name, file_size)
                disk_filename.unlink()
        if not self._temp_directory.is_dir():
            return
        for disk_filename in self._temp_directory.iterdir():
            if disk_filename.is_file():
                file_size = disk_filename.stat().st_size
                LOGGER.info('FileStorage: Remove temp file: "%s"; size: %d', disk_filename.name, file_size)
                disk_filename.unlink()

    @classmethod
    def _fname_original_to_disk(cls, original_filename: str) -> str:
        return cls._canonize_file(original_filename)

    @classmethod
    def _fname_url_to_disk(cls, url_filename: str) -> str:
        return cls._canonize_file(url_filename)

    @staticmethod
    def _fname_disk_to_url(disk_filename: str) -> str:
        return disk_filename

    @staticmethod
    def _fname_disk_to_display(disk_filename: str) -> str:
        return disk_filename

    @staticmethod
    def _canonize_file(filename: str) -> str:
        canonized = clean_filename(filename)
        if clean_filename(canonized) != canonized:
            raise Exception('clean_filename failed to canonize file name', filename)
        return canonized

    def _create_dirs(self) -> None:
        if not self._storage_directory.is_dir():
            self._storage_directory.mkdir(mode=0o755)

        if not self._temp_directory.is_dir():
            self._temp_directory.mkdir(mode=0o755)

    def _retention_thread_procedure(self) -> None:
        LOGGER.info('FileStorage: Retention thread started')
        previous_check_time: float = 0
        while True:
            try:
                now = time()
                if now - previous_check_time > 10 * 60:  # every 10 minutes
                    LOGGER.info('FileStorage: Check for outdated files')
                    previous_check_time = time()
                    self._check_retention()

                # Wait for 60 seconds with a possibility
                # to be interrupted through stop() call:
                with self._condition_stop:
                    if not self._stopping:
                        self._condition_stop.wait(60)
                    if self._stopping:
                        LOGGER.info('Retention thread found stop signal')
                        break
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception('FileStorage: Retention thread got exception: %s', repr(exc))
                sleep(60)  # prevent from flooding

    def _check_retention(self) -> None:
        now = time()
        if not self._storage_directory.is_dir():
            return
        for file in self._storage_directory.iterdir():
            if file.is_file():
                modified_unixtime = get_file_modified_unixtime(file)
                if now - modified_unixtime > self._max_store_time_seconds:
                    file_size = file.stat().st_size
                    LOGGER.info('FileStorage: Remove outdated file: "%s"; size: %d', file, file_size)
                    file.unlink()

        if not self._temp_directory.is_dir():
            return
        for file in self._temp_directory.iterdir():
            if file.is_file():
                modified_unixtime = get_file_modified_unixtime(file)
                if now - modified_unixtime > 15 * 60:  # every 15 minutes
                    file_size = file.stat().st_size
                    LOGGER.info('FileStorage: Remove outdated temp file: "%s"; size: %d', file, file_size)
                    file.unlink()
