## Synopsis


This repository contains the Ansible Roles for deploying OpenStack on given hardware, tested on Openstack Liberty->Newton on KVM and ESXi hypervisors.
The deployment mechanism for openstack is packstack but most of the work come from the BMaaS provided before hand and the ability to scale your cloud at will.


## Code Example

To deploy a full Cloud infrastructure certain requirements must be met (we'll go into those details later) and the Infrastructure must be described before running the actual deployment commands. These Ansible Roles can be modulated to achieve certain tasks, in this repository we have put together three sets of roles: Prepare the environment, Deploy the Systems and Provision the Cloud. Obviously it is possible to re-order those roles to fit a different environment.
Here are the Scripts and Roles provided for the Cloud Administrator.

-	Install the Operating System and OpenStack

{Ansible_playbooks_directory}/deploy_infrastructure.yml

## Motivation

As OpenStack Clouds need to be created in our environment, we need to ensure to have a reproducible and robust way to deploy OpenStack in a consistent manner. 
These Ansible Roles allow the Cloud Administrator to easily deploy Clouds with customizable parameters such as: type of networking (vlan, non-vlan, flat, etc.).

## Installation

To execute the Ansible Roles provided in this repository, the Cloud Administrator must fulfill the following requirements:
-	At least 1 Install Server, 1 Controller/Network node and 1 Compute node
-	The deployment manager needs access to the internet to create a local yum repo for install. After this all packages are locked down and have a repo nfs exported to each node from the Install Server.
-	The Install server is physically connected to the same network as the OpenStack nodes through the External and Internal networks - the minimal number of physical NICs must be reached

Typical workflow:
- git config --global http.sslVerify false
- git clone https://gitlab.com/jahorn/ansible_cloud.git
- cd ansible_openstack
-	The Install server installed with a RHEL derivative (VM or Baremetal).
-	The Install server is physically connected to the same network as the OpenStack nodes through the External and Internal networks in the same Layer-2 domain - the minimal number of physical NICs must be reached
    -	The interconnect switch shall allow untagged traffic and DHCP traffic
    -	Currently, the first drop on the servers shall be for the external management; the second drop is used for PXE booting
- edit bootstrap.sh (enable proxy etc..)
- ./bootstrap.sh
- ./deploy_utils_server.yml or ./deploy_utils_server_esxi.yml
- ./deploy_infrastructure.yml or deploy_infrastructure_esxi.yml
- ./provision_cloud.yml (configures tenant networking and external network while booting 2 vms to test each)

if you recieve a error relating trusted certificates:
  git config --global  http.sslVerify false
## Contributors

Jason Horn: jason.horn@gmail.com

- <Optional> ./provision_cloud.yml (configures tenant networking and external network while booting 2 vms to test each)


Then, execute the bootstrap.sh script to have the rest of the software requirements deployed.

If you recieve a error relating trusted certificates:
  git config --global  http.sslVerify false
