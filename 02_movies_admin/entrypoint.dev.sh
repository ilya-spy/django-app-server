#!/bin/sh

# Wait check database availability
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.5
    done
    printf "PostgreSQL started\n"
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


# Rest of migrations for all django apps
pipenv run python manage.py migrate


# Populate yearly markups
# SQL will make sure no duplications
pipenv run python manage.py dbquery --script ../01_schema_design/movies_database.mark.ddl


# Create super user (redo this in development mode only)
superuser () {
    local username="$1"
    local email="$2"
    local password="$3"

    cat <<EOF | pipenv run python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username="$username").exists():
    User.objects.create_superuser("$username", "$email", "$password")
    print('\nCreated superuser "{}". Django bringup done.'.format("$username"))
else:
    print('\nUser "{}" exists already, not created'.format("$username"))
EOF
}
# Use python commands in bash func to avoid errors in django on duplicated add
superuser \
"$DJANGO_SUPERUSER_USER" "$DJANGO_SUPERUSER_EMAIL" "$DJANGO_SUPERUSER_PASSWORD"


# Elastic initial setup (redo this in development mode only)
elasticsetup () {
    local index_name="$1"
    local schema_file="$2"

    cat <<EOF | pipenv run python manage.py shell
import sys
sys.path.append('../05_elastic')
from elastic import EsManager

esm = EsManager("$index_name")
esm.create_schema("$schema_file")
EOF
}
elasticsetup "movies" "../05_elastic/elastic.schema.json"


exec "$@"
