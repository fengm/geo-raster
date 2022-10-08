
FROM minfeng/geo-env:latest
LABEL creator Min Feng

ADD . /opt/lib
RUN cd /opt/lib && pip install -r requirements.txt && python setup.py install
RUN rm -rf /opt/lib
