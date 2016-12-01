#!/bin/bash
#
#PURPOSE: To find all packages needed by each openstack release
#HOWTO:
#  - repave at least 1 controller / 1 compute node
#  - install openstack manually (packstack)
#  - download /var/log/yum.log from the controller && compute nodes
#  - Parse each log 
#      - ssh compute1 "cat /var/log/yum.log" |awk -F': ' '{print $NF}'|awk -F'-[[:digit:]]' '{print $1}'|sed 's/^[[:digit:]]://g'|sort |uni
q > compute_pkg.list
#      - ssh controller1 "cat /var/log/yum.log" |awk -F': ' '{print $NF}'|awk -F'-[[:digit:]]' '{print $1}'|sed 's/^[[:digit:]]://g'|sort |
uniq > controller_pkg.list
#  - combine the controller package list with the compute package list
#      - sort compute_pkg.list controller_pkg.list |uniq > package.list
#  - run the following on a freshly paved blade to avoid errors with local rpm database
#      - cat package.list | while read rpm ; do
#           /usr/bin/yum  -y install    --downloaddir=$REPO_DIR --downloadonly $rpm | grep Installed || \
#           /usr/bin/yum  -y reinstall  --downloaddir=$REPO_DIR --downloadonly $rpm
#        done
#  - this file will generate the package list below and download to REPO_DIR
#    then pull this repo dir to the Deployment Managment server and createrepo
#
#
OPENSTACK_RELEASE="newton"
REPO_DIR="/var/www/html/rdolocal/$OPENSTACK_RELEASE/"
mkdir -p $REPO_DIR
cat package.list | while read rpm ; do
  /usr/bin/yum  -y install    --downloaddir=$REPO_DIR --downloadonly $rpm | grep Installed || \
  /usr/bin/yum  -y reinstall  --downloaddir=$REPO_DIR --downloadonly $rpm
done
