# Limbo file sharing (https://github.com/kolomenkin/limbo)
# Copyright 2018-2022 Sergey Kolomenkin
# Licensed under MIT (https://github.com/kolomenkin/limbo/blob/master/LICENSE)
#
from typing import Any, Callable, Union

import bottle


AnyFunction = Callable[..., Any]
RouteResponse = Union[bottle.HTTPResponse, bottle.HTTPError]


def bottle_route(route: str) -> Callable[[AnyFunction], AnyFunction]:
    return bottle.route(route)  # type: ignore


def bottle_view(template_file: str) -> Callable[[AnyFunction], AnyFunction]:
    return bottle.view(template_file)  # type: ignore


def bottle_get(url_path: str) -> Callable[[AnyFunction], AnyFunction]:
    return bottle.get(url_path)  # type: ignore


def bottle_post(url_path: str) -> Callable[[AnyFunction], AnyFunction]:
    return bottle.post(url_path)  # type: ignore
