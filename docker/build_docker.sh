#!/usr/bin/env bash
# Build the cyoa docker container. This will not work everywhere...

set -ex

# Get the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Build the docker file; make sure to set the context
cd ${DIR}/..
docker build -t banerjs/fault-isolation:cyoa_website -f docker/Dockerfile .
