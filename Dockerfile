FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:latest
MAINTAINER Theodoros Tsioutsias <theodoros.tsioutsias@cern.ch>

ARG BRANCH

RUN yum install --setopt=tsflags=nodocs -y \
    vim \
    git \
    python \
    python2-devel \
    python2-pip \
    gcc

RUN pip install --upgrade pip

RUN cd /opt && git clone -b ${BRANCH} https://gitlab.cern.ch/ttsiouts/aardvark.git
RUN cd /opt/aardvark && pip install -e .
