#!/bin/bash
set -e
export NODE_OPTIONS="--no-experimental-fetch"
git pull

source venv/bin/activate
pip install -r requirements.txt

npm ci --dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

python manage.py collectstatic --noinput

python manage.py migrate

sudo systemctl restart star-burger
