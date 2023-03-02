#!/bin/bash
set -e

while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
done

while ! nc -z $ES_HOST $ES_PORT; do
      sleep 0.1
done

while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 0.1
done

SCRIPT_PATH=$(dirname "${BASH_SOURCE[0]}")

. "$SCRIPT_PATH/set_etl_index.sh" $ES_HOST $ES_PORT

echo "Start project"

python main.py