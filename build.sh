#!/bin/sh
docker compose up --force-recreate --build -d
docker compose exec office /bin/bash -c 'python3 manage.py migrate'
docker compose exec office /bin/bash -c 'python3 manage.py collectstatic --no-input -v 3'
rm -r ./static
docker compose cp office:/app/static ./static
docker image prune -f
