#!/usr/bin/env bash

iruby register
./node_modules/.bin/ijs --ijs-install-kernel

jupyter notebook --no-browser --no-mathjax --ip=* --port $PORT

