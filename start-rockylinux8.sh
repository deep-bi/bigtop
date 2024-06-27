#!/bin/bash

mkdir -p cache/.gradle
mkdir -p cache/.m2

docker run --rm -u jenkins:jenkins \
    -v `pwd`:/ws \
    -v `pwd`/cache/.gradle:/var/lib/jenkins/.gradle \
    -v `pwd`/cache/.m2/:/var/lib/jenkins/.m2 \
    -it --workdir /ws bigtop/slaves:3.2.1-rockylinux-8 bash -l