FROM ubuntu:16.04
RUN mkdir /depsolver
WORKDIR /depsolver
RUN apt-get -y update && apt-get -y install \
  default-jdk \
  opam \
  python \
  python3 \
  haskell-platform \
  rustc \
  git \
  build-essential \
  m4
RUN opam init -y
RUN opam switch install 4.06.0
CMD /bin/bash
