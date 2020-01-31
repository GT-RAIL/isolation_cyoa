# Dockerfile to build the analysis app on top of the Django app for isolation

FROM nvidia/cuda:10.1-cudnn7-devel

# Args
ARG UID=1001

# Update apt, install conda and get packages. Also create a non-root user
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
        curl -O https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh && \
         sha256sum Anaconda3-2019.03-Linux-x86_64.sh && \
    bash Anaconda3-2019.03-Linux-x86_64.sh -b -p /opt/anaconda && \
    rm -rf /var/lib/apt/lists/* \
    cd / && \
        echo 'Defaults !secure_path' >> /etc/sudoers && \
        groupadd -g ${UID} banerjs && \
        useradd -rm -u ${UID} -g banerjs -G sudo,adm,cdrom,dip,plugdev banerjs && \
        echo "banerjs ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-dockersudo-ubuntu && \
        mkdir /notebooks && \
        chown -R banerjs:banerjs /notebooks

# Set the user, copy the code into the container
USER banerjs
ADD --chown=banerjs . /home/banerjs/website
ENV WEBSITE_WORKSPACE=/home/banerjs/website NOTEBOOKS_WORKSPACE=/notebooks

# Install the basics for data science followed by the website requirements
RUN cd /home/banerjs && \
    . /opt/anaconda/etc/profile.d/conda.sh && \
    conda init && \
    conda create -y -n venv && \
    conda activate venv && \
    conda install \
         graphviz \
         jupyter \
         matplotlib \
         numpy \
         pandas \
         psutil \
         scikit-learn \
         scipy \
         seaborn \
         sphinx && \
    sudo -H conda update -n base -c defaults conda && \
    conda install pytorch torchvision cudatoolkit=10.1 -c pytorch && \
    pip install -r requirements.txt && \
    pip install \
        visdom

# Small setup for QoL
RUN mkdir /home/banerjs/.saves && \
    ln -sf /home/banerjs/website/docker/.emacs /home/banerjs/

# Then run the expose settings for the django dev server
WORKDIR /notebooks
CMD ["python" "manage.py", "runserver", "0:8000"]
