import os
import socket
import time
from datetime import datetime
from typing import Any, List

from numpy import random


def log(*args: Any) -> None:
    # %(asctime)s000 - %(process)5d - %(name)s - %(levelname)s - %(message)s
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'), f'- {os.getpid(): >5} - hlp - INFO -', *args)


def get_random_bytes(size: int, seed: int) -> bytes:
    random.seed(seed)
    result = random.bytes(size)
    assert isinstance(result, bytes)
    return result


def get_random_text(size: int, seed: int) -> str:
    random.seed(seed)
    items: List[str] = []
    for char in range(ord('A'), ord('Z') + 1):
        items += chr(char)
    for char in range(ord('a'), ord('z') + 1):
        items += chr(char)
    for char in range(ord('0'), ord('9') + 1):
        items += chr(char)
    items.extend(('.', ',', ';', ':', '!',))
    items.extend((' ', ' ', ' ', ' ',))
    items += '\n'
    return ''.join(random.choice(items, size))


# https://gist.github.com/butla/2d9a4c0f35ea47b7452156c96a4e7b12
def wait_net_service(host: str, port: int, timeout: int) -> bool:
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (int): In seconds. How long to wait before raising errors.
    """
    log(f'Waiting for TCP server: {host}:{port} (timeout: {timeout} seconds)')

    start_time = time.perf_counter()
    while True:
        try:
            remaining = timeout - (time.perf_counter() - start_time)
            if remaining <= 0:
                log('ERROR! TCP connection timeout!')
                return False

            with socket.create_connection((host, port), timeout=remaining) as sock:
                log('TCP connection succeeded')
                sock.close()
                return True

        except OSError as ex:
            log(f'TCP connection failed: {ex!r}')
            time.sleep(0.1)
