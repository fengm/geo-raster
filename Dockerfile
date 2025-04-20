
FROM minfeng/geo-env:latest
LABEL creator Min Feng


RUN pip install cython
ADD . /opt/lib
RUN pip install /opt/lib
RUN rm -rf /opt/lib
