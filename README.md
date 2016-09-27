## Synopsis

This repository contains the Ansible Roles for deploying a full infrastructure from Operating System provisioning to running a VM in the OpenStack Cloud.

## Code Example

To deploy a full Cloud infrastructure certain requirements must be met (we'll go into those details later) and the Infrastructure must be described before running the actual deployment commands. These Ansible Roles can be modulated to achieve certain tasks, in this repository we have put together three sets of roles: Prepare the environment, Deploy the Systems and Provision the Cloud. Obviously it is possible to re-order those roles to fit a different environment.
Here are the Scripts and Roles provided for the Cloud Administrator.

-	Bootstrap the Install server (includes installing Ansible)

{Ansible_playbooks_directory}/bootstrap.sh

-	Configure the Ansible environment on the Install Server

{Ansible_playbooks_directory}/deploy_utils_server.yml

-	Install the Operating System and OpenStack

{Ansible_playbooks_directory}/deploy_infrastructure.yml

-	Provision the installed Cloud with external network, VXlan network, an image and two VMs

{Ansible_playbooks_directory}/provision_cloud.yml

## Motivation

As OpenStack Clouds need to be created in our environment, we need to ensure to have a reproducible and robust way to deploy OpenStack in a consistent manner. These Ansible Roles allow the Cloud Administrator to easily deploy Clouds with customizable parameters such as: type of networking (vlan, non-vlan, flat, etc.), type of systems (so far netra6000 blades and X5-2 servers are supported).

## Installation

To execute the Ansible Roles provided in this repository, the Cloud Administrator must fulfill the following requirements:
-	At least 1 Install Server, 1 Controller/Network node and 1 Compute node
-	The Install server must be installed with OL 7.2 (not tested with other version although it may work)
-	All nodes have access to the Internet to pull packages from Oracle Public Yum, EPEL and OpenStack RDO
-	The Install server is physically connected to the same network as the OpenStack nodes through the External and Internal networks - the minimal number of physical NICs must be reached

Then, execute the bootstrap.sh script to have the rest of the software requirements deployed.

If you recieve a error relating trusted certificates:
  git config --global  http.sslVerify false
## Contributors

Oracle CGBU - Platform Group

Jason Horn: jason.horn@oracle.com

JB Broccard: j.b.broccard@oracle.com

## License

This repository is intended only for Oracle CGBU use. Any use other than Oracle CGBU must be validated by Oracle CGBU Management.

