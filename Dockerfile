FROM ubuntu:18.04

RUN apt-get update \
 && apt-get upgrade --yes \
 && apt-get dist-upgrade --yes \
 && apt-get install -y  python3 python3-pip \
 && pip3 install pymysql flask flask-env click \
 && apt-get clean autoclean \
 && apt-get autoremove --yes \
 && rm -rf /var/lib/{apt,dpkg,cache,log}/ \
 && rm -fr /tmp/* /var/tmp/* 

ONBUILD RUN rm -rf /usr/share/doc/* \
  && rm -rf /usr/share/doc/*/copyright \
  && rm -rf /usr/share/man/* \
  && rm -rf /usr/share/info/* 




COPY app.py /opt/app.py
COPY templates /opt/templates
ENV FLASK_APP=/opt/app.py
WORKDIR "/opt/"
CMD ["python3", "/opt/app.py"]
