FROM python:3-alpine

RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
        gcc \
        musl-dev \
    && pip install \
        bottle==0.12.13 \
        streaming_form_data==0.6.1 \
    && pip install \
        flake8==3.5.0 \
        numpy==1.14.5 \
        pytest==3.6.1 \
        requests==2.18.4 \
    && pip install \
        cherrypy==8.9.1 \
        paste==2.0.3 \
        tornado==5.0.2 \
        twisted==18.4.0 \
        waitress==1.1.0 \
    && apk del \
        gcc \
        musl-dev \
    && apk add --no-cache \
        make \
    && mkdir -p -m 777 /tmp/storage

COPY . /opt/limbo/

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage

WORKDIR /opt/limbo
CMD make test
