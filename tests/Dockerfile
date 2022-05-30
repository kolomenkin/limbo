FROM python:3.7.6-alpine

RUN set -ex \
    && apk add --no-cache -- make \
    && apk add --no-cache --virtual=.build-essential -- \
        gcc \
        musl-dev

COPY \
    ./requirements.txt \
    /opt/limbo_dependencies/

RUN set -ex \
    && pip install \
        --requirement=/opt/limbo_dependencies/requirements.txt

COPY \
    ./requirements.dev.txt \
    /opt/limbo_dependencies/

RUN set -ex \
    && pip install \
        --requirement=/opt/limbo_dependencies/requirements.dev.txt

RUN set -ex \
    && apk del -- .build-essential \
    && mkdir --parents --mode=777 -- /tmp/storage

ENV PYTHONUNBUFFERED=1 \
    LIMBO_STORAGE_DIRECTORY=/tmp/storage

WORKDIR /opt/limbo

CMD ["make", "test"]

COPY \
    ./ \
    /opt/limbo/
