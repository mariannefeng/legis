# TODO: update pip version to be newer?

FROM ubuntu:latest

#RUN apt-get update -y
#RUN apt-get -y upgrade
#RUN apt-get install -y python-pip python-dev build-essential
RUN \
  apt-get update && \
  apt-get install -y python python-dev python-pip python-virtualenv && \
  rm -rf /var/lib/apt/lists/*

RUN pip install virtualenv
RUN mkdir -p /legis

COPY legis_view /legis/legis_view
COPY legis_data /legis/legis_data

COPY *.py /legis/
COPY *.sh /legis/
WORKDIR /legis
RUN virtualenv legis_env
RUN source /legis_env/bin/activate

WORKDIR /legis/legis_view
RUN pip install -r requirements.txt

WORKDIR /legis/legis_data
RUN pip install -r requirements.txt
RUN python nltk_setup.py

EXPOSE 5000
EXPOSE 5001

# turn on debugging for development
ENV FLASK_DEBUG=1
ENV PYTHON_UNBUFFERED=1

WORKDIR /legis
RUN chmod +x /legis/start.sh
#RUN /legis/start.sh
#CMD ["/bin/sh", "start.sh"]
ENTRYPOINT ["/bin/sh", "start.sh"]