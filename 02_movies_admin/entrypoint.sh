#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi


# Database content schema create
pipenv run python manage.py migrate movies 0001

# Populate yearly markups
# SQL will make sure no duplications
pipenv run python manage.py dbquery --script ../01_schema_design/movies_database.mark.ddl

# Rest of migrations for all django apps
pipenv run python manage.py migrate

# Create super user
pipenv run python manage.py createsuperuser --noinput \
    --username $DJANGO_SUPERUSER_USER \
    --email $DJANGO_SUPERUSER_EMAIL

exec "$@"