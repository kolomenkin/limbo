FROM python:3-alpine

COPY . /opt/limbo/

RUN pip install -r /opt/limbo/requirements.txt \
    && pip install cherrypy \
    && mkdir -p -m 777 /tmp/storage

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage \
    LIMBO_WEB_SERVER=cherrypy \
    LIMBO_LISTEN_HOST=0.0.0.0 \
    LIMBO_LISTEN_PORT=80

CMD python3 /opt/limbo/server.py

EXPOSE 80
