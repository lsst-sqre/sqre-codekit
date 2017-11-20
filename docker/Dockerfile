FROM docker.io/python:3.6.3
MAINTAINER sqre-admin

ARG CODEKIT_VER=3.1.0

USER root
RUN pip install sqre-codekit=="$CODEKIT_VER" --no-cache-dir

RUN useradd -m codekit
USER codekit

CMD ["/usr/local/bin/github-tag-version"]
