#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi


# Rest of migrations for all django apps
pipenv run python manage.py migrate

# Populate yearly markups
# SQL will make sure no duplications
pipenv run python manage.py dbquery --script ../01_schema_design/movies_database.mark.ddl


# Create super user
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
    print('User "{}" exists already, not created'.format("$username"))
EOF
}

# We use python commands in bash func to avoid errors in django on duplicated add
superuser \
"$DJANGO_SUPERUSER_USER" "$DJANGO_SUPERUSER_EMAIL" "$DJANGO_SUPERUSER_PASSWORD"

exec "$@"
