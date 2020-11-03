#!/usr/bin/sh

sudo apt-get install gcc python-pyparsing python-pyside pyside-tools libpython2.7-dev python-dev libboost-all-dev cmake python-pil python-numpy pypy cython libgsl-dev libopenscenegraph-dev pypy-setuptools python-setuptools libxml2-dev python-pygraphviz python-networkx pypy-dev python-thrift libqt4-dev libboost-all-dev pyside-tools uuid-dev
echo "Installing dependencies..."
sudo apt-get -y install libxml2-dev python-pip
git clone https://github.com/eleme/thriftpy.git
cd thriftpy
sudo pypy setup.py install
sudo make clean
sudo python setup.py install
git clone https://bitbucket.org/pypy/numpy.git
cd numpy
sudo pypy setup.py install
