
FROM minfeng/geo-env:latest
LABEL creator Min Feng

ADD . /opt/lib
RUN pip install /opt/lib
RUN rm -rf /opt/lib
