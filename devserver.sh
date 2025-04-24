#!/bin/sh
source .venv/bin/activate
export FLASK_APP=main
export FLASK_DEBUG=1
export PORT=5000
nohup flask run -p $PORT > nohup.out 2>&1 &
