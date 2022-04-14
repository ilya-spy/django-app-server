
FROM admin.panel.base.img

COPY ./01_schema_design /srv/01_schema_design
COPY ./02_movies_admin /srv/02_movies_admin
COPY ./03_sqlite_to_postgres /srv/03_sqlite_to_postgres

RUN echo Easy. Jedi business >> /srv/file.txt
VOLUME /srv 