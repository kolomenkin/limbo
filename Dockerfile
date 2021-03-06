FROM python:3.7-alpine

COPY *.py \
    requirements.txt \
    /opt/limbo/

COPY static /opt/limbo/static/

RUN set -ex \
    && apk add --no-cache \
        gcc \
        libffi-dev \
        musl-dev \
        openssl-dev \
    && pip install -r /opt/limbo/requirements.txt \
    && pip install cherrypy==8.9.1 \
    && apk del \
        gcc \
        libffi-dev \
        musl-dev \
        openssl-dev \
    && mkdir -p -m 777 /tmp/storage

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage \
    LIMBO_WEB_SERVER=cherrypy \
    LIMBO_LISTEN_HOST=0.0.0.0 \
    LIMBO_LISTEN_PORT=80

CMD python3 /opt/limbo/server.py

EXPOSE 80
