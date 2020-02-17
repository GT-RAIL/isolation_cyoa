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
    cd / && \
        echo 'Defaults !secure_path' >> /etc/sudoers && \
        groupadd -g ${UID} banerjs && \
        useradd -rm -u ${UID} -g banerjs -G sudo,adm,cdrom,dip,plugdev banerjs && \
        echo "banerjs ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-dockersudo-ubuntu && \
        mkdir /notebooks && \
        chown -R banerjs:banerjs /notebooks

# Set the user, copy the code into the container
USER banerjs

# Install the basics for data science
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
    pip install \
        visdom && \
    sudo -H conda update -n base -c defaults conda && \
    conda install pytorch torchvision cudatoolkit=10.1 -c pytorch

# Install the basics for the website; Django, etc.
ADD --chown=banerjs . /home/banerjs/website
ENV WEBSITE_WORKSPACE=/home/banerjs/website NOTEBOOKS_WORKSPACE=/notebooks
RUN cd /home/banerjs/website && \
    . /opt/anaconda/etc/profile.d/conda.sh && \
    conda activate venv && \
    pip install -r requirements.txt && \
    pip install \
        researchpy==0.1.8 \
        statsmodels==0.11.0

# Small updates for QoL
RUN mkdir /home/banerjs/.saves && \
    ln -sf /home/banerjs/website/docker/.emacs /home/banerjs/

# Then run the expose settings for the django dev server
WORKDIR /notebooks
COPY docker/entrypoint.sh /venv_entrypoint.sh
ENTRYPOINT ["/venv_entrypoint.sh"]
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8000"]
