#!/bin/bash
set -e

echo "Source conda"
source /opt/anaconda/etc/profile.d/conda.sh && conda activate venv
(cd $NOTEBOOKS_WORKSPACE && pip install -e .) || (cd $NOTEBOOKS_WORKSPACE && sudo -H pip install -e .) || echo "Unexpected virtualenv"
export PATH=$HOME/.local/bin:$PATH
exec "$@"
