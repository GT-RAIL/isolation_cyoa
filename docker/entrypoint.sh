#!/bin/bash
set -e

echo "Source conda"
source /opt/anaconda/etc/profile.d/conda.sh && conda activate venv
(ls venv/data && pip install -e .) || (ls venv/data && sudo -H pip install -e .) || echo "Unexpected virtualenv"
export PATH=/home/banerjs/.local/bin:$PATH
exec "$@"
