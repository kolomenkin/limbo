import socket
from time import strftime, sleep, time
from typing import Any, Optional, List

from numpy import random


def log(*args: Any) -> None:
    print(strftime('%Y-%m-%d %H:%M:%S     - hlp - INFO -'), *args)


def get_random_bytes(size: int, seed: int) -> bytes:
    random.seed(seed)
    result = random.bytes(size)
    assert isinstance(result, bytes)
    return result


def get_random_text(size: int, seed: int) -> str:
    random.seed(seed)
    items: List[str] = []
    for char in range(ord('A'), ord('Z')+1):
        items += chr(char)
    for char in range(ord('a'), ord('z')+1):
        items += chr(char)
    for char in range(ord('0'), ord('9')+1):
        items += chr(char)
    items.extend(('.', ',', ';', ':', '!', ))
    items.extend((' ', ' ', ' ', ' ', ))
    items += '\n'
    return ''.join(random.choice(items, size))


# http://code.activestate.com/recipes/576655-wait-for-network-service-to-appear/
def wait_net_service(host: str, port: int, timeout: Optional[int] = None) -> bool:
    log(f'Waiting for web server: {host}:{port}')

    sock = socket.socket()
    end = time() + timeout if timeout else 0

    while True:
        try:
            if timeout:
                if time() > end:
                    log('ERROR! Network sockets connect waiting timeout!')
                    return False

            sock.connect((host, port))

        except socket.timeout:
            sleep(0.1)
        except socket.error:
            sleep(0.1)

        else:
            sock.close()
            return True
