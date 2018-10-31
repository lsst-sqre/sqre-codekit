FROM docker.io/python:3.6.3

ARG CODEKIT_VER=4.0.1

USER root
RUN pip install sqre-codekit=="$CODEKIT_VER" --no-cache-dir

RUN useradd -m codekit
USER codekit
WORKDIR /home/codekit

CMD ["/usr/local/bin/github-tag-release"]
