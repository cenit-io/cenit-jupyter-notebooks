#!/usr/bin/env bash

npm install -g ijavascript

jupyter notebook --no-browser --no-mathjax --ip=* --port $PORT
