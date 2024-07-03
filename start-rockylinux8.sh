#!/bin/bash

mkdir -p cache/.gradle
mkdir -p cache/.m2

podman run --rm -u jenkins:jenkins --userns=keep-id \
    -v `pwd`:/ws:z \
    -v `pwd`/cache/.gradle:/var/lib/jenkins/.gradle:z \
    -v `pwd`/cache/.m2/:/var/lib/jenkins/.m2:z \
    -it --workdir /ws bigtop/slaves:3.2.1-rockylinux-8 bash -l
