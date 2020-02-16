FROM python:3.7.6-alpine

RUN set -ex \
    && apk add --no-cache \
        gcc \
        libffi-dev \
        make \
        musl-dev \
        openssl-dev

COPY \
    ./requirements.txt \
    ./requirements.dev.txt \
    /opt/limbo_dependencies/

RUN set -ex \
    && pip install \
        -r /opt/limbo_dependencies/requirements.txt \
        -r /opt/limbo_dependencies/requirements.dev.txt \
    && mkdir -p -m 777 /tmp/storage

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage

WORKDIR /opt/limbo

CMD ["make", "test"]

COPY \
    ./ \
    /opt/limbo/
