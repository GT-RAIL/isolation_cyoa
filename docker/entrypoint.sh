#!/bin/bash
set -e

echo "Source conda"
unset PYTHONPATH
source /opt/anaconda/etc/profile.d/conda.sh && conda activate venv
(cd $NOTEBOOKS_WORKSPACE && pip install -e .) || (cd $NOTEBOOKS_WORKSPACE && sudo -H pip install -e .) || echo "Unexpected virtualenv"
export PATH=$HOME/.local/bin:$PATH

# Settings for django
export PYTHONPATH=$WEBSITE_WORKSPACE
export DJANGO_SETTINGS_MODULE="website.settings"
export DJANGO_ALLOW_ASYNC_UNSAFE="true"

exec "$@"
