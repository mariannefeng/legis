#!/bin/sh

CONTAINER_ID=$(docker ps -aqf "name=legis-mock")

if [ ! -z "$CONTAINER_ID" ]; then
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    docker ps
fi
