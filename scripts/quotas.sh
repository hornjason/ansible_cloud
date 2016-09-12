demo_tenant=$(openstack project show -f value -c id demo)
mgmt_tenant=$(openstack project show -f value -c id mgmt)

nova quota-update --instances 100 --cores 100 --ram 512000 --injected-files 50  $demo_tenant
nova quota-update --instances 100 --cores 100 --ram 512000 --injected-files 50  $mgmt_tenant
neutron quota-update --network 20 --port 100 --subnet 50 $demo_tenant
neutron quota-update --network 20 --port 100 --subnet 50 $mgmt_tenant

