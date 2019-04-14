
FROM geographica/gdal2:latest

LABEL creator Min Feng
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y awscli cython python-psycopg2 python-boto python-pandas python-setuptools python-pip
RUN pip install watchtower

WORKDIR /opt

ENV G_INI=/opt/ini
ENV G_LOG=/opt/log
ENV G_TMP=/opt/tmp

ADD . /opt/lib
RUN cd /opt/lib && python setup.py install
RUN rm -rf /opt/lib

ENTRYPOINT []
