#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Start the search ETL daemom
# Rest of migrations for all django apps
pipenv run python manage.py dbexport -d --interval 10 &

pipenv run python manage.py runserver $DJANGO_HOST:$DJANGO_PORT &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?

exec "$@"
