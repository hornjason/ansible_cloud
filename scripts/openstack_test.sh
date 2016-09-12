#!/bin/bash
 
source ~/keystonerc_admin || exit 1
 
QCOW2_URL="http://10.240.199.2/image/myOL6image.qcow2"
yum install -y sshpass
/usr/bin/sshpass -p 'changeme' scp 172.31.254.254:/var/lib/images/*qcow2 .
 
echo "Loading image OL6.6 with Cloud-Init inside"
ret=$(nova image-list | grep testVMimage | wc -l)
if [ $ret -eq 0 ] ; then
    wget http://10.240.199.2/image/myOL6image.qcow2
    glance image-create --name testVMimage --disk-format qcow2 --container-format bare --owner $(openstack project list | awk '/admin/{print $2}') --file myOL6image.qcow2 --visibility public --progress
fi
echo "Image loaded, hit enter to continue"
 
# vlan provider
echo "About to create PROVIDER VLAN network 587"
neutron net-create ext-net --provider:network_type vlan --provider:physical_network physnet1 --provider:segmentation_id 587 --shared --router:external
neutron subnet-create --name ext-subnet --gateway 10.240.121.65 --allocation-pool start=10.240.121.80,end=10.240.121.126 --dns-nameserver 8.8.8.8 --ip-version 4 --disable-dhcp ext-net 10.240.121.64/26
echo "PROVIDER VLAN network 587 created, hit enter to continue"
 
 
# vxlan tenant
echo "About to create TENANT VxLAN network"
neutron net-create demo-vxlan-net --provider:network_type vxlan
neutron subnet-create --name demo-vxlan-subnet --disable-dhcp --gateway 192.168.200.1 demo-vxlan-net 192.168.200.0/24
neutron router-create demo-vxlan-router
neutron router-interface-add demo-vxlan-router demo-vxlan-subnet
neutron router-gateway-set demo-vxlan-router ext-net
echo "TENANT VxLAN network created, hit enter to continue"
 
# unlock security
echo "About to create rules for ICMP and SSH"
nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0
nova secgroup-add-rule default tcp 22 22 0.0.0.0/0    
nova secgroup-add-rule default tcp 80 80 0.0.0.0/0    
echo "rules created, hit enter to continue"
 
echo "Now creating VMs"
nova boot --flavor m1.medium --image testVMimage --nic net-id=$(neutron net-list| awk '/ext-net/ {print $2}') --min-count 40 extnet-vm

nova boot --flavor m1.medium --image testVMimage --nic net-id=$(neutron net-list| awk '/demo-vxlan-net/ {print $2}') --min-count 100 vxlan-vm
