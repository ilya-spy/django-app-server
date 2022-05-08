
# this is to showcase docker layers approach to minimize layers delta
# image names should be unified in composer
FROM django.app.server.base

RUN apk update && \
    apk add gettext

# create directory for the user
RUN mkdir -p /home/app

# create the group and the user
RUN addgroup -S app && adduser -S app -G app
RUN chown app:app -R /home/app && \
    chown app:app -R /usr/src/srv/02_movies_admin

USER app
ENV HOME /home/app
ENV DATABASE postgres

ENV HOSTNAME app
ENV ALLOWED_HOSTS 127.0.0.1
RUN env

# work with django app service
WORKDIR /usr/src/srv/02_movies_admin
RUN pipenv install

# Config Locales
RUN pipenv run python manage.py makemessages --all && \
    pipenv run python manage.py compilemessages

# copy updated entrypoint
COPY ./02_movies_admin/entrypoint.prod.sh .

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.prod.sh"]