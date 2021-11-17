FROM docker.io/python:3.8

ARG CODEKIT_VER=4.0.1

USER root
RUN pip install sqre-codekit=="$CODEKIT_VER" --no-cache-dir
# hadolint ignore=DL3059
RUN useradd -m codekit
USER codekit
WORKDIR /home/codekit

CMD ["/usr/local/bin/github-tag-release"]
