
FROM geographica/gdal2:latest

LABEL creator Min Feng
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y awscli cython python-psycopg2 python-boto python-pandas python-setuptools

WORKDIR /opt

ADD . /opt/lib
RUN cd /opt/lib/git/geo-raster && python setup.py install
RUN rm -rf /opt/lib
