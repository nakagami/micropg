#!/bin/bash
sudo apt install build-essential libreadline-dev libffi-dev git pkg-config
git clone --recurse-submodules https://github.com/micropython/micropython.git micropython_src
cd micropython_src/ports/unix
make
cp micropython ../../..
