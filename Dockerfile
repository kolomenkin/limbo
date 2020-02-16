FROM python:3.7.6-alpine

COPY \
    ./requirements.txt \
    /opt/limbo_dependencies/

RUN set -ex \
    && apk add --no-cache \
        gcc \
        libffi-dev \
        musl-dev \
        openssl-dev \
    && pip install \
        -r /opt/limbo_dependencies/requirements.txt \
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

CMD ["python", "/opt/limbo/server.py"]

EXPOSE 80

COPY \
    ./static/ \
    /opt/limbo/static/

COPY \
    ./*.py \
    /opt/limbo/
