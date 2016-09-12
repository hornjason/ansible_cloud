OVS_CONF_FILE=/etc/neutron/plugins/ml2/openvswitch_agent.ini
ML2_CONF_FILE=/etc/neutron/plugins/ml2/ml2_conf.ini
NOVA_CONF="/etc/nova/nova.conf"
CONTROLLER_LAB_IP="100.65.194.206"
INTERFACES_TEMPLATE_FILE=/usr/share/nova/interfaces.template

cp $INTERFACES_TEMPLATE_FILE $INTERFACES_TEMPLATE_FILE.orig

function getip () {
 ip a show $1|awk '/inet / {gsub(/\/.*/, "");print $2}'
}
 # update httpd horizon
  echo "Updating Horizon with natt'd address"
  sed -i "/## Server aliases/a \  ServerAlias $CONTROLLER_LAB_IP" /etc/httpd/conf.d/15-horizon_vhost.conf

# VNC
  echo "Updating novnc_procy_base_url in nova.conf"
  crudini --set --existing $NOVA_CONF vnc novncproxy_base_url http://$CONTROLLER_LAB_IP:6080/vnc_auto.html
  openstack-config --set $NOVA_CONF DEFAULT  novncproxy_host 0.0.0.0
  openstack-config --set $NOVA_CONF DEFAULT  novncproxy_port 6080
  openstack-config --set $NOVA_CONF DEFAULT  vncserver_listen $(getip ens3f0.586)
  openstack-config --set $NOVA_CONF DEFAULT  vncserver_proxyclient_address $(getip ens3f0.586)
  openstack-config --set $NOVA_CONF DEFAULT  vnc_enabled True
   

 # each node is a network node :)
  yum install -y openstack-neutron-ml2
 
  crudini --set $OVS_CONF_FILE ovs local_ip $(getip ens3f0.16)
  crudini --set $ML2_CONF_FILE ml2 type_drivers vxlan,vlan,local
  crudini --set $ML2_CONF_FILE ml2 tenant_network_types vxlan,local
  crudini --set $ML2_CONF_FILE ml2_type_vlan network_vlan_ranges physnet1:1000:2000
  crudini --set $ML2_CONF_FILE securitygroup enable_security_group True
  crudini --set $ML2_CONF_FILE ml2 mechanism_drivers openvswitch,l2population
  crudini --set $ML2_CONF_FILE ml2_type_vxlan vni_ranges 1001:2000
  crudini --set $ML2_CONF_FILE ml2_type_vxlan vxlan_group 239.1.1.1
  crudini --set $ML2_CONF_FILE securitygroup enable_ipset True
   
  crudini --set $OVS_CONF_FILE ovs enable_tunneling True
  crudini --set $OVS_CONF_FILE agent tunnel_types vxlan
  crudini --set $OVS_CONF_FILE agent l2_population True
  crudini --set $OVS_CONF_FILE agent prevent_arp_spoofing True
  crudini --set $OVS_CONF_FILE ovs bridge_mappings physnet1:br-ex

  ln -s $ML2_CONF_FILE /etc/neutron/plugin.ini
 
#
#   Update the Open vSwitch configuration file to set the bridge mappings which PackStack failed to do
#
 
#
#   Update the network interface configuration file template to be used when injecting
#   network interface configuration within a VM instance

# create br-ex on each node 
     /usr/bin/ovs-vsctl add-br br-ex 
     /usr/bin/ovs-vsctl add-port br-ex ens3f1
	 
	 


# Enable config drive
#
crudini --set $NOVA_CONF DEFAULT force_config_drive True
 
#
# Enable injection of the network interfaces into VM instances
#
crudini --set $NOVA_CONF DEFAULT flat_injected True


cat <<EOT> $INTERFACES_TEMPLATE_FILE
{% for ifc in interfaces %}
DEVICE="{{ ifc.name }}"
NM_CONTROLLED="no"
ONBOOT=yes
TYPE=Ethernet
BOOTPROTO=none
IPADDR={{ ifc.address }}
NETMASK={{ ifc.netmask }}
BROADCAST={{ ifc.broadcast }}
GATEWAY={{ ifc.gateway }}
{% endfor %}
EOT



openstack-service restart
