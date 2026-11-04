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

export $(grep -v '^#' .env | xargs)
ROLLBAR_TOKEN=$ROLLBAR_ACCESS_TOKEN
REVISION=$(git rev-parse HEAD)

curl -s https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ROLLBAR_TOKEN \
  -F environment=production \
  -F revision=$REVISION \
  -F local_username=root
