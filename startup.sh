#!/usr/bin/env bash

npm install -g ijavascript

ijs notebook --no-browser --no-mathjax --ip=* --port $PORT
