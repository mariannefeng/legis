#!/bin/sh

### YA GOTTA HAVE PYTHON 3 INSTALLED ###
export FLASK_DEBUG=1

# do cleanup on exit
cleanup()
{
    unset FLASK_DEBUG
    local pids=$(jobs -pr)
    [ -n "$pids" ] && kill $pids
}
trap cleanup EXIT

export PYTHONPATH=${PWD}
python3 --version
echo "===STARTING LEGIS==="
python3 legis_data/tastydata.py &
echo "===STARTED DATA SERVICE==="
python3 legis_view/legis.py &
echo "===STARTED VIEW==="
wait
