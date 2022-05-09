
# this is to showcase docker layers approach to minimize layers delta
# image names should be unified in composer
FROM django.app.server.make

# copy hot updates to source, not requiring rebuild
COPY ./01_schema_design          /usr/src/srv/01_schema_design
COPY ./02_movies_admin           /usr/src/srv/02_movies_admin
COPY ./03_sqlite_to_postgres     /usr/src/srv/03_sqlite_to_postgres

# workaround permissions
USER root
RUN chown app:app -R /usr/src/srv
USER app

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.prod.sh"]
