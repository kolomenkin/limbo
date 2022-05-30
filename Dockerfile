FROM python:3.10.4-alpine3.16

COPY \
    ./requirements.txt \
    /opt/limbo_dependencies/

RUN set -ex \
    && apk add --no-cache --virtual=.build-essential -- \
        gcc \
        musl-dev \
    && pip install \
        --requirement=/opt/limbo_dependencies/requirements.txt \
    && apk del -- .build-essential \
    && mkdir --parents --mode=777 -- /tmp/storage

ENV PYTHONUNBUFFERED=1 \
    LIMBO_STORAGE_DIRECTORY=/tmp/storage \
    LIMBO_WEB_SERVER=cheroot \
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
