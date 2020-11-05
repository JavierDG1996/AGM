#Download base image robocomp 18.04
FROM robocomp:bionic_fcl

# LABEL about the custom image
LABEL maintainer="emartinena@unex.es"
LABEL version="0.1"
LABEL description="This is custom Docker Image for Robocomp in Ubuntu Focal"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt update && apt install -y sudo vim

# Replace 1000 with your user / group id
RUN export uid=1000 gid=1000 && \
    mkdir -p /home/robolab && \
    echo "robolab:x:${uid}:${gid}:Robolab,,,:/home/robolab:/bin/bash" >> /etc/passwd && \
    echo "robolab:x:${uid}:" >> /etc/group && \
    echo "robolab ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/robolab && \
    chmod 0440 /etc/sudoers.d/robolab && \
    chown ${uid}:${gid} -R /home/robolab


    
# Install AGM dependencies
RUN sudo apt-get install -y gcc python-pyparsing python-pyside pyside-tools libpython2.7-dev python-dev libboost-all-dev cmake python-pil python-numpy pypy cython libgsl-dev libopenscenegraph-dev pypy-setuptools python-setuptools libxml2-dev python-pygraphviz python-networkx pypy-dev python-thrift libqt4-dev libboost-all-dev pyside-tools uuid-dev
RUN sudo apt-get -y install libxml2-dev python-pip
USER robolab
ARG AGM_VER=unknown
RUN git clone https://github.com/ljmanso/AGM.git
RUN git clone https://github.com/eleme/thriftpy.git
RUN git clone https://bitbucket.org/pypy/numpy.git
USER root
RUN cd thriftpy && pypy setup.py install && make clean && python setup.py install
RUN cd numpy && pypy setup.py install
RUN echo "/usr/local/lib/" >> /etc/ld.so.conf
RUN ldconfig
USER robolab
ENV HOME /home/robolab/
ENV LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:AGM
ENV ROBOCOMP /home/robolab/robocomp/ 
RUN export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:AGM
RUN export HOME=/home/robolab/
# Installing agm
RUN cd AGM && mkdir -p build
RUN cd AGM/build && pwd && cmake .. -DROBOCOMP_SUPPORT=True -DPYTHON_BINDINGS=False && make -j1 && sudo make install

