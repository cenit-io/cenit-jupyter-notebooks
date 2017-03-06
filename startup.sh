#!/usr/bin/env bash

# Register ruby kernel
iruby register

# Register nodejs kernel
./node_modules/.bin/ijs --ijs-install-kernel

# Register bash kernel
python -m bash_kernel.install

# Startup jupyter notebook application.
jupyter notebook --no-browser --no-mathjax --ip=* --port $PORT

