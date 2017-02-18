FROM ubuntu:latest

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential

COPY clouds /app/clouds
COPY static /app/static
COPY templates /app/templates
COPY *.py /app/
COPY test_cache.sqlite /app/
COPY requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt
RUN python nltk_setup.py
EXPOSE 5000

# turn on debugging for development
ENV FLASK_DEBUG=1
ENV PYTHON_UNBUFFERED=1
ENV FLASK_APP=legis.py

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]