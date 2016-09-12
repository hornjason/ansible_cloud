compute_hosts="c00b06 c00b07 c00b08 c00b09"
ssh_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "

for host in  $compute_hosts; do
  sshpass -p 'changeme' ssh $ssh_args $host " sed -i '/^ *- name: cpu_source$/{n;s/interval: 600$/interval: 60/}' /etc/ceilometer/pipeline.yaml"
  sshpass -p 'changeme' ssh $ssh_args $host 'systemctl restart openstack-ceilometer-compute'
done
