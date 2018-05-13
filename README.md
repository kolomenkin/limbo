# Limbo: the file sharing lightweight service

This project implements lightweight web page with easy possibility to upload, download, list, remove files.
It requires no login.
All files are automatically deleted 24 hours after upload.

## Configuration

### Config file

You can edit config.py to set custom options.

### Environment variables

* LIMBO_WEB_SERVER : default value is 'wsgiref'
* LIMBO_LISTEN_HOST : default value is 'localhost'
* LIMBO_LISTEN_PORT : default value is '8080'
* LIMBO_STORAGE_DIRECTORY : default value is './storage'
* LIMBO_MAX_STORAGE_SECONDS : default value is '86400'
* LIMBO_IS_DEBUG : default value is '0'

## How to run the service

1. Copy files from this repo
2. Install service dependecies
    ```
    python3 -m pip install -r requirements.txt
    ```
3. Run the service:
    ```
    python3 duplo.py
    ```
4. Open web page http://localhost:8080/

### Docker

The following command will build docker image and will run container listening on localhost:8080.
After container is stopped it will be automatically deleted with all currently stored files.
Don't forget to elevate priviledges before running docker! (sudo)

```
docker run --rm -it -p 127.0.0.1:8080:80 $(docker build --quiet .)
```

The following usage will do the same but will also mount persistent directory for stored files (~/limbo_storage).

```
docker run --rm -it -p 127.0.0.1:8080:80 -v ~/limbo_storage:/tmp/storage $(docker build --quiet .)
```

### Run in Windows

You can also run the service in Windows by the following command:
```
run-server-on-windows.cmd
```
