## Welcome to django-app-server package

This package serves as a pre-configured dockerised django web data management app.
It uses nginx as a static web reverse proxy for fast processing,
django to implement apis and views, and postgres db for persistent storage
 
Root directory contains services available to deploy.
Each service has corresponding Dockerfile.
Alltogether, services could be deployed as a web/app/db cluster automatically, using a Docker Composer setup provided below.

Good luck in exploring django-app-server!  

#### Full rebuild docker composer bundle
`docker-compose build --force-rm --no-cache`

#### Incremental build bundle
`docker-compose build`

#### Run build stages and development server (local environment)
`docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d [ --build ]`

#### Run composer services prepare for internet (production environment)
`docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d [ --build ]`

#### Superuser app is created for you. To change password
`docker exec -it admin_panel-app-1 pipenv run python manage.py changepassword app`

#### Import test films data
`docker exec -it admin_panel-app-1 pipenv run python manage.py dbimport --sqlite ../03_sqlite_to_postgres/db.sqlite`

#### Make locales
`docker exec -it admin_panel-app-1 pipenv run python manage.py makemessages --all`  
`docker exec -it admin_panel-app-1 pipenv run python manage.py compilemessages`

#### Bring docker bundle instance down amd remove volumes (WARNING: erase data)
`docker-compose down --remove-orphans [ -v ] [ --rmi all ]`

<br/>

### Run database service standalone
Run database instance before spawning up the application server  
<br/>
`docker volume create --name admin_panel_volume_db`

`docker run -d --name admin_panel-db-1 -p 5432:5432
  -v admin_panel_volume_db:/var/lib/postgresql/data
  -e POSTGRES_PASSWORD=123qwe
  -e POSTGRES_USER=app
  -e POSTGRES_DB=movies_database
  postgres:13.0-alpine`

### Run application server standalone
Run database instance before spawning up the application server  
<br/>
`docker volume create --name admin_panel_volume_app`

`docker run -d --name admin_panel-app-1 -p 5000:5000
  -v admin_panel_volume_app:/var/lib/django/data
  -e SECRET_KEY='django-insecure-+4d=$n@a)f#6nib1chzrotc*=7r%_womjssj5+_%tjg2ch@x=='
  -e ALLOWED_HOSTS='127.0.0.1 localhost *'
  -e DEBUG=True
  -e POSTGRES_PASSWORD=123qwe
  -e POSTGRES_USER=app
  -e POSTGRES_DB=movies_database
  -e POSTGRES_HOST=admin_panel-db-1
  -e POSTGRES_PORT=5432
  -e DJANGO_SUPERUSER_USER=app
  -e DJANGO_SUPERUSER_EMAIL=test@test.ru
  -e DJANGO_SUPERUSER_PASSWORD=123qwe
  django.app.server.app`
