#!/usr/bin/sh

sudo apt-get install --yes gcc python3-pyparsing libpyside2-dev pyside2-tools libpython3-dev python3-dev libboost-all-dev cmake python3-pil python3-numpy pypy3 cython libgsl-dev libopenscenegraph-dev python3-setuptools libxml2-dev python3-pygraphviz python3-networkx pypy3-dev python3-thrift libboost-all-dev uuid-dev qtbase5-dev qttools5-dev-tools python3-thriftpy libxml2-dev python3-pip


wget https://bootstrap.pypa.io/get-pip.py -o get-pip.py
pypy3 get-pip.py

sudo pypy3 -m pip install thriftpy
sudo pypy3 -m pip install numpy
