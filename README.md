# Isolation CYOA Website

The code here contains the Django webserver to present a CYOA style website to participants and collect data on the paths chosen.

Locally, the code uses docker to run; remote uses Heroku. Large files are stored on Dropbox.

## Local Developement

Ensure you have the webserver docker image. Either `docker pull banerjs/fault_isolation:cyoa_website` or run `./docker/build_docker.sh`. Make sure that you have a `.env` file with the appropriate client secrets available locally.

Run a postgres container:

```bash
docker run -d --rm --name postgres postgres:11
```

Then run the docker container. To run in interactive mode: `./docker/run_docker_interactive.sh`.
