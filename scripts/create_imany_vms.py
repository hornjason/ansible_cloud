source /var/lib/openstack/keystonerc_cloud_admin
PROJET_ID=$(openstack project list | awk '/admin/ {print $2}')
nova quota-update --instances 1000 --cores 1000 --ram 5120000 --floating-ips 1000 --fixed-ips 1000 --metadata-items 10240 --injected-files 500 ${PROJET_ID}
nova quota-show --tenant admin

neutron quota-update --port 10000
neutron quota-update --tenant-id admin --network 2000 --subnet 5000 --port 10000
nova flavor-create --swap 0 m1.prettysmall 1001 512 10 1

nova boot --min-count 95 --flavor m1.prettysmall --image testVMimage \
	--nic net-id=$(neutron net-list| awk '/ext-net/{print $2}') \
	--nic net-id=$(neutron net-list| awk '/vxlan/{print $2}') \
	dual-nic-vm

# ERROR (Forbidden): Quota exceeded for cores, instances, ram: Requested 280, 140, 573440, but already used 4, 2, 8192 of 20, 10, 51200 cores, instances, ram (HTTP 403) (Request-ID: req-e6782117-255d-4df7-a2f4-265227e71a26)

nova boot --min-count 100 --flavor m1.prettysmall --image testVMimage \
	--nic net-id=$(neutron net-list| awk '/vxlan/{print $2}') \
	vxlan-vm

