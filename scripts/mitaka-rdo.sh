#!/bin/bash
systemctl disable firewalld
systemctl stop firewalld
systemctl disable NetworkManager
systemctl stop NetworkManager
systemctl start network


yum install -y https://rdoproject.org/repos/rdo-release.rpm
#yum install -y centos-release-openstack-mitaka
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y --enablerepo=ol7_optional_latest install openstack-packstack
#sudo yum update -y
#sudo yum install -y openstack-packstack
#packstack --allinone
