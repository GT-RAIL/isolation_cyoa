# Isolation CYOA Website

The code here contains the Django webserver to present a CYOA style website to participants and collect data on the paths chosen. This work is presented in RO-MAN 2020.

Locally, the code uses docker to run; remote it uses Heroku (check the instructions for running [Django on Heroku](https://devcenter.heroku.com/categories/working-with-django)). Large files are stored on Dropbox.


## Local Development

Ensure you have the webserver docker image. Run `./docker/build_docker.sh website`. Make sure that you have a `.env` file with the appropriate client secrets available locally. An example `.env`:

```
# The environment that this .env file corresponds to
ENVIRONMENT=dev

# Django secret key
SECRET_KEY='some_secret'

# The local database URL
DATABASE_URL='postgres://banerjs:some_password@0.0.0.0:5432/cyoa'

# Dropbox Keys
DROPBOX_APP_KEY=some_dbx_key
DROPBOX_APP_SECRET=some_dbx_secret
DROPBOX_ACCESS_TOKEN=some_dbx_token
```

Run a postgres container `./docker/run_postgres.sh`

To connect to the database for the first setup: `docker exec -it postgres psql -U postgres`. Then run (for example):

```sql
CREATE USER banerjs WITH PASSWORD 'some_password';
ALTER USER banerjs WITH createdb createrole;
CREATE DATABASE cyoa;
ALTER DATABASE cyoa OWNER TO banerjs;
```

In subsequent connections, you can then use `./docker/run_postgres.sh` to connect directly to the database.

Then run the docker container. I prefer to run in interactive mode using: `./docker/run_website_interactive.sh`. The script mounts the appropriate host directories for me.


## Analysis

The bulk of the analysis for the paper was done in R with the R-Notebooks available in the `notebooks` directory. However, if one is so inclined, one can also use IPython notebooks. There is an IPython notebook docker image availabe too. To build it, run `./docker/build_docker.sh analysis`. Then run the notebook with `./docker/run_notebook.sh`. Subsequent uses of the run script will exec you into the running notebook container. (By default, the scripts assume the presence of nvidia-docker; if you don't have it, then remove the associated GPU flags from the `analysis.dockerfile` and the `run_notebook.sh` scripts).

The data for the analysis has been copied into the `data` folder for the public release of this repo. However note that the code in this codebase often points to hardcoded paths on my local machine where the data is originally fetched from. I apologize in advance for the headaches that this will cause.

The data is the output of running `python manage.py create_csv` on the Heroku database on which the RO-MAN 2020 experiment was conducted. There is no identifiable information available in those CSVs. If you are curious what columns in the CSV correspond to what columns / attributes in the database, then take a look at `dining_room/stats/data_loader.py`.
