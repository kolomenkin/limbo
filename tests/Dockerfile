FROM python:3.7-alpine

# streaming_form_data>=1.1.0 is needed to support Python 3.7
# The following error occurs on older version during package install:
#
# streaming_form_data/_parser.c:7741:13: error: too many arguments to function '(PyObject * (*)(PyObject *, PyObject * const*, Py_ssize_t))meth'
#      return (*((__Pyx_PyCFunctionFast)meth)) (self, args, nargs, NULL);
#             ~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# error: command 'gcc' failed with exit status 1

RUN set -ex \
    && apk add --no-cache \
        gcc \
        musl-dev \
        make \
    && pip install \
        bottle==0.12.13 \
        streaming_form_data==1.1.0 \
        flake8==3.5.0 \
        numpy==1.16.0 \
        pytest==3.6.1 \
        requests==2.20.0 \
        cherrypy==8.9.1 \
        paste==2.0.3 \
        tornado==5.0.2 \
        twisted==19.2.1 \
        waitress==1.1.0 \
    && apk del \
        gcc \
        musl-dev \
    && mkdir -p -m 777 /tmp/storage

COPY . /opt/limbo/

ENV LIMBO_STORAGE_DIRECTORY=/tmp/storage

WORKDIR /opt/limbo
CMD make test
