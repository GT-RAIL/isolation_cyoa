# Dockerfile to build the Django app for CYOA Isolation

FROM python:3.7

# Args
ARG UID=1001

# Update apt and get packages. Also create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        emacs25-nox \
        git \
        libpq-dev \
        nano \
        postgresql-client \
        python3-dev \
        sudo \
        unzip \
        uuid-dev \
        vim && \
    cd / && \
        echo 'Defaults !secure_path' >> /etc/sudoers && \
        groupadd -g ${UID} banerjs && \
        useradd -rm -u ${UID} -g banerjs -G sudo,adm,cdrom,dip,plugdev banerjs && \
        echo "banerjs ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-dockersudo-ubuntu

# Set the user, copy the code into the container
USER banerjs
ADD --chown=banerjs . /home/banerjs/website
ENV WEBSITE_WORKSPACE=/home/banerjs/website
WORKDIR /home/banerjs/website

# Then install django, psycopg2, etc.
RUN sudo -H pip install -r requirements.txt

# Small setup for QoL
RUN mkdir /home/banerjs/.saves && \
    ln -sf /home/banerjs/website/docker/.emacs /home/banerjs/

# Then run the expose settings for the django dev server
CMD ["python" "manage.py", "runserver", "0:8000"]
