#!/bin/sh

# run in mock mode with ./start.sh --mock

### YA GOTTA HAVE PYTHON 3 INSTALLED ###
export FLASK_DEBUG=1
export PYTHONPATH=${PWD}

# do cleanup on exit
cleanup()
{
    unset FLASK_DEBUG
    local pids=$(jobs -pr)
    [ -n "$pids" ] && kill $pids

    /bin/bash legis_data/wiremock/stop-mock.sh
}
trap cleanup EXIT

python3 --version

if [ $# -eq 0 ]; then
    echo "not mock"
    python3 legis_data/tastydata.py &
else
    # start backend accordingly
    for var in "$@"
    do
        if [ $var = "--mock" ]; then
            echo "mock"
            /bin/bash legis_data/wiremock/start-mock.sh
        else
            echo "not mock"
            python3 legis_data/tastydata.py &
        fi
    done
fi

# start view
python3 legis_view/legis.py &
wait
