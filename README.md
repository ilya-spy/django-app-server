### Welcome to django-app-server package

This package serves as a pre-configured dockerised django web data management app.
It uses nginx as a static web reverse proxy for fast processing,
django to implement apis and views, and postgres db for persistent storage
 
Root directory contains services available to deploy.
Each service has corresponding Dockerfile.
Alltogether everything could be deployed as a web/app/db cluster automatically.

Good luck in exploring django-app-server!

### Full Re-build docker images bundle
`docker build --no-cache -f Dockerfile.base -t django.app.server.base .`
`docker-compose build --force-rm --no-cache`

### Incremental build bundle
`docker build -f Dockerfile.base -t django.app.server.base .`
`docker-compose build`

### Run docker composer on a local server
`docker-compose up -d [ --build ]`

### Superuser app is created for you. Need to activate with password
`docker exec -it admin_panel_app_1 pipenv run python manage.py changepassword app`

### Bring docker bundle instance down amd remove volumes
`docker-compose down -v --remove-orphans`