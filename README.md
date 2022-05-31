# Limbo: the file sharing lightweight service

[![GitHub license](https://img.shields.io/github/license/kolomenkin/limbo)](LICENSE)
[![GitHub latest tag](
https://img.shields.io/github/v/tag/kolomenkin/limbo?sort=semver)](
https://github.com/kolomenkin/limbo/releases)
[![GitHub code size in bytes](
https://img.shields.io/github/languages/code-size/kolomenkin/limbo)](
https://github.com/kolomenkin/limbo/archive/refs/heads/master.zip)
[![Docker Image Size (tag)](
https://img.shields.io/docker/image-size/kolomenkin/limbo/latest)](
https://hub.docker.com/r/kolomenkin/limbo/tags?page=1&name=latest)
[![GitHub branch checks state](
https://img.shields.io/github/checks-status/kolomenkin/limbo/master)](
https://github.com/kolomenkin/limbo/commits/master)

| Branch      | CI Build Status using raw Python environments                                                                                                                                                                | CI Build Status using Docker images                                                                                                                                                                              |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **master**  | [![CI status](https://github.com/kolomenkin/limbo/actions/workflows/python-raw.yml/badge.svg?branch=master)](https://github.com/kolomenkin/limbo/actions/workflows/python-raw.yml?query=branch%3Amaster)     | [![CI status](https://github.com/kolomenkin/limbo/actions/workflows/python-docker.yml/badge.svg?branch=master)](https://github.com/kolomenkin/limbo/actions/workflows/python-docker.yml?query=branch%3Amaster)   |
| **develop** | [![CI status](https://github.com/kolomenkin/limbo/actions/workflows/python-raw.yml/badge.svg?branch=develop)](https://github.com/kolomenkin/limbo/actions/workflows/python-raw.yml?query=branch%3Adevelop)   | [![CI status](https://github.com/kolomenkin/limbo/actions/workflows/python-docker.yml/badge.svg?branch=develop)](https://github.com/kolomenkin/limbo/actions/workflows/python-docker.yml?query=branch%3Adevelop) |

This project implements lightweight web page with easy possibility
to upload, download, list, remove files.  
It requires no login.  
All files are automatically deleted 24 hours after upload.

- Change log: [CHANGELOG.md](CHANGELOG.md)
- Credits: [CREDITS](CREDITS)

## Requirements

- Python 3.7 - 3.10
- Dockerhub official image: <https://hub.docker.com/repository/docker/kolomenkin/limbo>
- Requirements for production: [requirements.txt](requirements.txt)
- Additional requirements for development: [requirements.dev.txt](requirements.dev.txt)

## Configuration

### Config file

You can edit [config.py](config.py) to set custom options. All of them may be
overloaded using environment variables.

### Environment variables

- `LIMBO_WEB_SERVER`  
    Default value is `wsgiref`. Python web server name. `wsgiref` is available by
    default. Other values will need installing appropriate python component.
    Supported values: `wsgiref`, `paste`, `cheroot`, ...
- `LIMBO_LISTEN_HOST`  
    Default value is `localhost`. IP address to listen.
    Usually `127.0.0.1` or `localhost` should be used for local testing, `0.0.0.0` for production.
- `LIMBO_LISTEN_PORT`  
    Default value is `8080`. IP port to listen (HTTP). Usually port `80` is used on production.
- `LIMBO_STORAGE_DIRECTORY`  
    Default value is `./storage`. Directory to store uploaded files in.
    If not exists it will be created automatically with access rights 755.
    This may be absolute path of path relative to Limbo root directory.
- `LIMBO_STORAGE_WEB_URL_BASE`  
    Default value is empty string. Allows to specify alternative web url
    to read files stored in `STORAGE_DIRECTORY` through HTTP/HTTPS.
    It is expected this URL is served by standalone web server.
    Empty string disables this setting. Value requires ending `/` character.
- `LIMBO_MAX_STORAGE_SECONDS`  
    Default value is `86400`. Time duration in seconds after which
    uploaded file will be automatically removed. `86400` seconds is equal to 24 hours.
    Automatic file purging happens approximately every 10 minutes.
- `LIMBO_IS_DEBUG`  
    Default value is `0`. Enable debug mode in bottle web framework.
    It will disable web page template caching.

## How to run the service

1. Copy files from this repo
1. Install service dependencies

    ```bash
    pip install -r requirements.txt
    ```

1. Run the service:

    ```bash
    python server.py
    ```

1. Open web page <http://localhost:8080/>

### Docker

The following command will build docker image and will run container listening on localhost:8080.  
After container is stopped it will be automatically deleted with all currently stored files.  
Don't forget to elevate privileges before running docker! (sudo)

```bash
docker run --rm -it -p 127.0.0.1:8080:80 $(docker build --quiet .)
```

The following usage will do the same but will also mount persistent directory
for stored files (`~/limbo_storage`).

```bash
docker run --rm -it -p 127.0.0.1:8080:80 -v ~/limbo_storage:/tmp/storage $(docker build --quiet .)
```

Run Limbo self-tests in docker:

```bash
docker run --rm -it $(docker build --file=tests/Dockerfile --quiet .)
```

### Run in Windows

You can also run the service in Windows by the following command:

```bash
run-server-on-windows.cmd
```

### Choosing underlying web server

Here is a number of bottle-compliant WSGI web servers tested with Limbo.
Particular web server versions can be checked in [requirements.dev.txt](requirements.dev.txt)

- wsgiref - logging to console, does not support async post body reading
- cheroot (ex-cherrypy) - works, no logging to console
- tornado - no logging to console, does not support big file upload (100+ MB)
- twisted - slow works, no logging to console, very slow
  (ignores async nature of streaming_form_data)
- waitress - slow works, no logging to console, very slow
  (ignores async nature of streaming_form_data)
- paste - partly works, logging to console, but no support for utf-8 in URLs
- flup - starts and do not handle any requests (Windows). All HTTP requests are hanging
- gevent - can't resolve dependencies in Windows in runtime
- gunicorn - can't resolve dependencies in Windows in runtime

## Testing the service

1. Copy files from this repo
1. Install service dependencies

    ```bash
    pip install -r requirements.txt -r requirements.dev.txt -r requirements.func.txt
    ```

1. Check syntax:

    ```bash
    make -- check-all-docker
    make -- check-all
    ```

1. Run unit tests locally:

    ```bash
    make test
    ```

### Running tests in Docker

```bash
docker build --pull --file=./tests/Dockerfile -- .
docker run --rm --tty --network=none "$(docker build --file=./tests/Dockerfile --quiet -- .)" make test
```
