#!/bin/sh

docker run -d --name legis-mock \
  -p 5000:8080 \
  -v $PWD/legis_data/wiremock/data:/home/wiremock \
  -e uid=$(id -u) \
  rodolpheche/wiremock \
     --verbose

