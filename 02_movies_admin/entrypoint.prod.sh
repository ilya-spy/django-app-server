#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

#  Wait check search availability
if [ "$SEARCHENGINE" = "elastic" ]
then
    echo "Waiting for Elasticsearch availability...";
    while ! nc -z $ELASTIC_HOST $ELASTIC_PORT; do
      sleep 0.5
    done
    printf "Elasticsearch started\n";
fi

# Run gunicorn
pipenv run gunicorn config.wsgi:application --bind $DJANGO_HOST:$DJANGO_PORT &

# Start the search ETL daemom
# Rest of migrations for all django apps
pipenv run python manage.py dbexport -d --interval 10 &


# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?

exec "$@"
