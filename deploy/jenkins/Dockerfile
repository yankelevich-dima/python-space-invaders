FROM jenkins

USER root


RUN apt-get update && apt-get install -y python-pip libffi-dev libssl-dev python-dev ansible rsync python-virtualenv openvpn
RUN pip install --upgrade cffi setuptools flake8


# install docker binaries

RUN curl -L https://github.com/docker/compose/releases/download/1.8.0/docker-compose-`uname -s`-`uname -m` > /usr/bin/docker-compose
RUN chmod +x /usr/bin/docker-compose
RUN curl -L https://get.docker.com/builds/Linux/x86_64/docker-latest.tgz > /tmp/docker-latest.tgz
RUN tar -xzf /tmp/docker-latest.tgz -C /tmp
RUN cp /tmp/docker/docker /usr/bin/docker
RUN chmod +x /usr/bin/docker
