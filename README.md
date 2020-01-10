# Isolation CYOA Website

The code here contains the Django webserver to present a CYOA style website to participants and collect data on the paths chosen.

Locally, the code uses docker to run; remote uses Heroku. Large files are stored on Dropbox.


## Local Developement

Ensure you have the webserver docker image. Either `docker pull banerjs/fault_isolation:cyoa_website` or run `./docker/build_docker.sh`. Make sure that you have a `.env` file with the appropriate client secrets available locally.

Run a postgres container:

```bash
docker run -d --rm --name postgres -p 5432:5432 postgres:11
```

To connect to the database for the first setup: `docker exec -it postgres psql -U postgres`. Then run:

```sql
CREATE USER banerjs WITH PASSWORD 'IsolationCYOA';
ALTER USER banerjs WITH createdb createrole;
CREATE DATABASE cyoa;
```

In subsequent connections, you can then use `docker exec -it postgres psql -U banerjs -d cyoa` to connect directly to the database.

Then run the docker container. To run in interactive mode: `./docker/run_docker_interactive.sh`.


## Notes

- In case we need to switch to websockets, then [this blog post](https://blog.heroku.com/in_deep_with_django_channels_the_future_of_real_time_apps_in_django) on Django channels might be a good place to start
- List of posts for configuring Django with Heroku:
    - https://devcenter.heroku.com/articles/django-app-configuration
    - https://devcenter.heroku.com/articles/django-assets
    - https://devcenter.heroku.com/articles/python-concurrency-and-database-connections