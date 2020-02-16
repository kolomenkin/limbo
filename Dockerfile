FROM python:3.7.4-alpine3.10

COPY \
    ./requirements.txt \
    /opt/limbo/

RUN apk add --no-cache \
        gcc \
        musl-dev \
    && pip install \
        -r /opt/limbo/requirements.txt \
        cherrypy==8.9.1 \
    && apk del \
        gcc \
        musl-dev \
    && mkdir -p -m 777 /tmp/storage

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage \
    LIMBO_WEB_SERVER=cherrypy \
    LIMBO_LISTEN_HOST=0.0.0.0 \
    LIMBO_LISTEN_PORT=80

CMD python3 /opt/limbo/server.py

EXPOSE 80

COPY *.py \
    /opt/limbo/

COPY static /opt/limbo/static/
