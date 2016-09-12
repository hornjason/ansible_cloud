#!/bin/bash
source /var/lib/openstack/keystonerc_cloud_admin
yum install dos2unix -y
 
nova list | awk '/ACTI/{print "nova delete " $2}' > /tmp/.delete_vms
sh /tmp/.delete_vms
 
#nova image-list | awk '/ACTI/{print "nova image-delete " $2}' > /tmp/.delete_images
#sh /tmp/.delete_images
 
# deleting network components
#neutron port-list -f value -F id| awk '{print "neutron port-update "$1}' > /tmp/.clear_ports.tmp
#neutron port-list | awk '/subnet_id/{print "neutron port-update "$2}' > /tmp/.clear_ports.tmp
neutron port-list -f csv -F id  | awk -F\" '!/id/{print "neutron port-update "$2}' > /tmp/.clear_ports.tmp
dos2unix /tmp/.clear_ports.tmp && awk '{print $0" --device_owner clear"}' /tmp/.clear_ports.tmp > /tmp/.clear_ports
sh /tmp/.clear_ports
 
#neutron port-list -f value -F id| awk '{print "neutron port-delete " $1}' > /tmp/.delete_ports
#neutron port-list | awk '/subnet_id/{print "neutron port-delete " $2}' > /tmp/.delete_ports
neutron port-list -f csv -F id| awk -F\" '!/id/{print "neutron port-delete "$2}' > /tmp/.delete_ports
dos2unix /tmp/.delete_ports && sh /tmp/.delete_ports
 
#neutron subnet-list | awk '/start/{print "neutron subnet-delete " $2}' > /tmp/.delete_subnets
neutron subnet-list -f csv -F id | awk -F\" '!/id/{print "neutron subnet-delete "$2}' > /tmp/.delete_subnets
dos2unix /tmp/.delete_subnets && sh /tmp/.delete_subnets
 
#neutron net-list | awk '/\//{print "neutron net-delete " $2}' > /tmp/.delete_nets
neutron net-list -f csv -F id | awk -F\" '!/id/{print "neutron net-delete "$2}' > /tmp/.delete_nets
dos2unix /tmp/.delete_nets && sh /tmp/.delete_nets
 
neutron router-gateway-clear demo-vxlan-router
neutron router-list ; ret=$? ; if [ $ret -ne 0 ] ; then
    ID=$(neutron router-port-list demo-vxlan-router | grep 192.168 | awk '{print $8}'|sed -e 's/"//g' -e 's/,//g')
    neutron router-interface-delete demo-vxlan-router $ID
    neutron router-gateway-clear demo-vxlan-router
    neutron router-delete demo-vxlan-router
fi
 
neutron router-list | awk '/demo/{print "neutron router-delete " $2}' > /tmp/.delete_routers
dos2unix /tmp/.delete_routers && sh /tmp/.delete_routers
 
for i in /tmp/.delete_ports /tmp/.delete_subnets /tmp/.delete_nets ; do sh $i ; done
