
FROM geographica/gdal2:latest

MAINTAINER Min Feng
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y awscli cython python-psycopg2 python-boto python-pandas python-setuptools

ADD . /opt

ENV G_INI=/opt/ini
RUN cd /opt && python setup.py install

