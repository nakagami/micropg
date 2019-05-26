#!/bin/bash
sudo apt install build-essential libreadline-dev libffi-dev git pkg-config python
git clone --recurse-submodules https://github.com/micropython/micropython.git micropython_src
cd micropython_src/ports/unix
make axtls
make
cp micropython ../../..
