#!/usr/bin/env python

import argparse
import ipaddress
import json
import mmirequests
import os
import sys
import time
import yaml

import sshtools

from os import environ as env
from xml.etree import ElementTree as ET

mmirequests.sslVerifyCertificate = False


import keystoneclient.v2_0.client as ksclient
import heatclient.client as heatclient
import novaclient.client as novaclient
import neutronclient.neutron.client as neutronclient

from keystoneclient.auth.identity import v2
from keystoneclient import session


def configureTopology(noafloatingip, topologyInfo, stackname):
    """ Configures the topology on the given NOAM """
    url = "https://{0}/mmi/alexa/v1.0/bulk/configurator".format(noafloatingip)
    print "Configuring NOA using the bulk configurator MMI..."

    # Actually send the configurator request
    xmlstring = getBulkConfiguratorXml(topologyInfo)
    resp = mmirequests.post(url, data=xmlstring)
    with open("/tmp/{0}.xml".format(stackname), 'w') as f:
        f.write(xmlstring)

    try:
        r = resp.json()

        for message in r['messages']:
            print message['message']
            if 'details' in message:
                for detail in message['details']:
                    print detail

    except Exception as ex:
        print ex

def getBulkConfiguratorXml(topologyInfo):
    """ Return the bulk configuration XML for the given topology"""
    configtree = ET.Element('configuration')
    topotree = ET.SubElement(configtree, 'topo')
    for ne in topologyInfo['networkelements']:
        elem = ET.SubElement(topotree, 'networkElement')
        ET.SubElement(elem, 'name').text = ne['name']

    for sg in topologyInfo['servergroups']:
        elem = ET.SubElement(topotree, 'serverGroup')
        ET.SubElement(elem, 'name').text = sg['name']
        ET.SubElement(elem, 'level').text = sg['level']
        ET.SubElement(elem, 'parentSgName').text = sg['parentSgName']
        ET.SubElement(elem, 'functionName').text = sg['functionName']
        ET.SubElement(elem, 'numWanRepConn').text = str(sg['numWanRepConn'])

    for s in topologyInfo['services']:
        svc = ET.SubElement(topotree, 'servicePath')
        ET.SubElement(svc, 'name').text = s['name']
        ET.SubElement(svc, 'intraSitePath').text = s['intraSitePath']
        ET.SubElement(svc, 'interSitePath').text = s['interSitePath']

    for server in topologyInfo['servers']:
        out = ET.SubElement(topotree, 'server')
        ET.SubElement(out, 'hostname').text           = server['hostname']
        ET.SubElement(out, 'networkElementName').text = server['networkElementName']
        ET.SubElement(out, 'serverGroupName').text    = server['serverGroupName']
        ET.SubElement(out, 'profileName').text        = server['profileName']
        if 'haRolePref' in server and server['haRolePref']:
            ET.SubElement(out, 'haRolePref').text = server['haRolePref']
        ET.SubElement(out, 'location').text = server['location']
        ET.SubElement(out, 'role').text     = server['role']
        ET.SubElement(out, 'systemId').text = server['systemId']

        ntp = ET.SubElement(out, 'ntpServers')
        ntp = ET.SubElement(ntp, 'ntpServer')
        ET.SubElement(ntp, 'ipAddress').text = server['ntpServerIp']
        ET.SubElement(ntp, 'prefer').text = 'true'

    for networkDevice in topologyInfo['networkDevices']:
        devout = ET.SubElement(topotree, 'networkDevice')
        ET.SubElement(devout, 'port').text     = networkDevice['port']
        ET.SubElement(devout, 'type').text     = networkDevice['type']
        ET.SubElement(devout, 'hostname').text = networkDevice['hostname']
        intf = ET.SubElement(devout, 'interfaces')
        intf = ET.SubElement(intf, 'interface')

        ET.SubElement(intf, 'ipAddress').text   = networkDevice['ipAddress']
        ET.SubElement(intf, 'networkName').text = networkDevice['networkName']

        opts = ET.SubElement(devout, 'options')
        ET.SubElement(opts, 'onboot').text = 'true'
        ET.SubElement(opts, 'bootProto').text = 'none'

    for network in topologyInfo['networks']:
        cnt = 0
        vlanId = network['vlanId']
        neName = network['neName']

        if network['shared']:
            loop = 1
        else:
            loop = 0

        while cnt <= loop:
            #print "BEGIN: CNT {2} LOOP {3} NENAME: {0} NAME: {4} VLAN: {1}".format(neName,vlanId,cnt,loop,network['name']) 
            out = ET.SubElement(topotree, 'network')
            ET.SubElement(out, 'name').text = network['name']

            if neName != "GLOBAL":
                 ET.SubElement(out, 'neName').text = neName

            ET.SubElement(out, 'vlanId').text = str(vlanId)
            ET.SubElement(out, 'ipAddress').text = network['ipAddress']
            ET.SubElement(out, 'subnetMask').text = network['subnetMask']

            #gateway = network['gateway']

            if not network['routed']:
                ET.SubElement(out, 'isDefault').text = 'false'
            else:
                ET.SubElement(out, 'gatewayAddress').text = network['gateway']
                ET.SubElement(out, 'isDefault').text = 'true'

            if network['neName'] != "GLOBAL":
                ET.SubElement(out, 'isRoutable').text = 'true'
                ET.SubElement(out, 'locked').text = 'true'
            else:
                ET.SubElement(out, 'isRoutable').text = 'false'
                ET.SubElement(out, 'locked').text = 'false'
            
            cnt += 1
            neName = "SO_NE{0}".format(cnt)
            #vlanId += 20
            
            #print "END: CNT {2} LOOP {3} NAME: {0} VLAN: {1}".format(neName,vlanId,cnt,loop) 

    return ET.tostring(configtree)

def configure():
    parser = argparse.ArgumentParser(description="Configures a stack created using stackcreate.py")
    parser.add_argument("stackname", help="Name of the stack to configure.", type=str)
    parser.add_argument("keyfile", help="Path to SSH key to use for authentication.", type=str)
    parser.add_argument("-g", "--generate_only", help="Generate XML only", action="store_true")
    args = parser.parse_args()

    print "checking OpenStack environment settings..."
    osauthurl    = env.get('OS_AUTH_URL', False)
    osusername   = env.get('OS_USERNAME', False)
    ospassword   = env.get('OS_PASSWORD', False)
    ostenantname = env.get('OS_TENANT_NAME', False)
    osregionname = env.get('OS_REGION_NAME', False)

    if not osauthurl:
        print "OS_AUTH_URL must be set! Did you source an openrc file?"
        sys.exit(-1)
    if not osusername:
        print "OS_USERNAME must be set! Did you source an openrc file?"
        sys.exit(-1)
    if not ospassword:
        print "OS_PASSWORD must be set! Did you source an openrc file?"
        sys.exit(-1)
    if not ostenantname:
        print "OS_TENANT_NAME must be set! Did you source an openrc file?"
        sys.exit(-1)
    if not osregionname:
        print "OS_REGION_NAME must be set! Did you source an openrc file?"
        sys.exit(-1)

    print "creating CLI client objects..."
    keystone = ksclient.Client(auth_url=osauthurl,
                               username=osusername,
                               password=ospassword,
                               tenant_name=ostenantname,
                               region_name=osregionname)

    auth = v2.Password(auth_url=osauthurl,
                       username=osusername,
                       password=ospassword,
                       tenant_name=ostenantname)

    sess  = session.Session(auth=auth)
    token = keystone.auth_token

    heaturl = keystone.service_catalog.get_endpoints()['orchestration'][0]['publicURL']
    heat = heatclient.Client('1', endpoint=heaturl, token=token)
    nova = novaclient.Client('2.1', session=sess)
    neutron = neutronclient.Client('2.0', session=sess)

    # allnets    = neutron.list_networks()
    # allservers = nova.servers.list()
    servers      = {}
    nets         = {}

    print "checking status of stack..."
    stack = heat.stacks.get(args.stackname)

    while stack.to_dict()['stack_status'] == 'CREATE_IN_PROGRESS':
        stack = heat.stacks.get(args.stackname)
        status = stack.to_dict()['stack_status']
        print "Stack is in state '{0}'".format(status)
        if status == 'CREATE_FAILED':
            print 'Stack creation failed!'
            sys.exit(-1)
        time.sleep(3)

    # stack = heat.stacks.get(stackname)
    noafloatingip = None
    soafloatingip = None

    for output in stack.outputs:
        if output['output_key'] == 'floatingip_noa':
            noafloatingip = output['output_value']
        if output['output_key'] == 'floatingip_soa1':
            soafloatingip = output['output_value']

    resources = heat.resources.list(args.stackname)

    hostmap = {}

    print "Fetching application configuration data..."
    vlanId = 2

    topologyInfo = {}
    topologyInfo['networkelements'] = []
    topologyInfo['servergroups']    = []
    topologyInfo['services']        = []
    topologyInfo['servers']         = []
    topologyInfo['networkDevices']  = []
    topologyInfo['networks']        = []

    for r in resources:
        if r.resource_type == "OS::Nova::Server":
            meta = heat.resources.metadata(args.stackname, r.resource_name)
            server = nova.servers.get(r.physical_resource_id).to_dict()
            server['awmeta'] = meta
            if not meta['extra']:
                servers[server['name']] = server
            if meta['noa']:

                # elem = ET.SubElement(configtree, 'configHostname')
                # ET.SubElement(elem, 'hostname').text = server['name']

                for ne in meta['appworks']['networkelements']:
                    networkElementInfo         = {}
                    networkElementInfo['name'] = ne['name']
                    topologyInfo['networkelements'].append(networkElementInfo)

                for sg in meta['appworks']['servergroups']:
                    serverGroupInfo                  = {}
                    serverGroupInfo['name']          = sg['name']
                    serverGroupInfo['level']         = sg['level']
                    serverGroupInfo['parentSgName']  = sg['parentSgName']
                    serverGroupInfo['functionName']  = sg['functionName']
                    serverGroupInfo['numWanRepConn'] = str(sg['numWanRepConn'])
                    topologyInfo['servergroups'].append(serverGroupInfo)

                for s in meta['appworks']['services']:
                    serviceInfo                  = {}
                    serviceInfo['name']          = s['name']
                    serviceInfo['intraSitePath'] = s['intraSitePath']
                    serviceInfo['interSitePath'] = s['interSitePath']
                    topologyInfo['services'].append(serviceInfo)

        elif r.resource_type == "OS::Neutron::Net":
            meta = heat.resources.metadata(args.stackname, r.resource_name)
            net = neutron.show_network(r.physical_resource_id)['network']
            #print "network: {0}".format(net)
            net['awmeta'] = meta
            net['awmeta']['vlanId'] = vlanId
            vlanId += 1

            # Only 1 subnet per network for now
            net['subnet'] = neutron.show_subnet(net['subnets'][0])['subnet']
            nets[net['name']] = net

    mplist = []

    for servername in servers:
        server = servers[servername]
        
        serverInfo                       = {}
        serverInfo['hostname']           = servername
        serverInfo['networkElementName'] = server['awmeta']['neName']
        serverInfo['serverGroupName']    = server['awmeta']['sgName']
        serverInfo['profileName']        = server['awmeta']['hwprofile']
        serverInfo['haRolePref']         = server['awmeta'].get('haRolePref', None)
        serverInfo['location']           = 'OpenStack'
        serverInfo['role']               = server['awmeta']['role']
        serverInfo['systemId']           = 'OpenStack'
        # Only single NTP server is supported
        # serverInfo['ntpServerIp']        = '192.168.56.180'
        serverInfo['ntpServerIp']        = '10.250.32.10'
        topologyInfo['servers'].append(serverInfo)

        if server['awmeta']['role'] == "roleMP":
            mplist.append(servername)
        #JTH
        vlanId = 5
        for netname in server['addresses']:
            try:
                net = nets[netname]
            except:
                #print netname
                net = neutron.show_network(netname)
                net['awmeta'] = { "shared": false, "neName": GLOBAL, "routed": false, "shared": false }
                net['awmeta']['vlanId'] = vlanId
                vlanId += 1

                # Only 1 subnet per network for now
                subnet, trash = netname.split('-', 2)
                net['subnet'] = neutron.show_subnet(subnet + '-subnet')['subnet']
                nets[net['name']] = net

            #print(netname)

            networkDeviceInfo             = {}
            networkDeviceInfo['port']     = server['awmeta']['portmap'][net['awmeta']['name']]
            networkDeviceInfo['type']     = 'Ethernet'
            networkDeviceInfo['hostname'] = servername

            interfaces = server['addresses'][netname]
            for interface in interfaces:
                if interface['OS-EXT-IPS:type'] == 'fixed':
                    addr = interface['addr']
                    break

            # Single IP per device
            networkDeviceInfo['ipAddress']   = addr
            networkDeviceInfo['networkName'] =  net['awmeta']['name']

            if net['subnet']['gateway_ip']:
                hostmap[servername] = addr
                if server['awmeta']['noa']:
                    noaip = addr
                    noahostname = servername

            topologyInfo['networkDevices'].append(networkDeviceInfo)


    for netname in nets:
        net                       = nets[netname]

        networkInfo               = {}
        networkInfo['name']       = net['awmeta']['name']
        networkInfo['neName']     = net['awmeta']['neName']
        networkInfo['vlanId']     = net['awmeta']['vlanId']
        #JTH to allow multiple sites sharing xmi/imi
        networkInfo['shared']     = net['awmeta']['shared']
        networkInfo['routed']     = net['awmeta']['routed']

        networkAddr               = ipaddress.ip_network(net['subnet']['cidr'])
        networkInfo['ipAddress']  = str(networkAddr.network_address)
        networkInfo['subnetMask'] = str(networkAddr.netmask)

        networkInfo['gateway']    = net['subnet']['gateway_ip']

        topologyInfo['networks'].append(networkInfo)
        
    


    if args.generate_only:
        print getBulkConfiguratorXml(topologyInfo)
        sys.exit(0)

    #getBulkConfiguratorXml(topologyInfo)
    #xmlstring = getBulkConfiguratorXml(topologyInfo)
    #with open("/tmp/{0}.xml".format(args.stackname), 'w') as f:
    #    f.write(xmlstring)

    hoststr = ""
    nodestr = ""

    for host in hostmap:
        hoststr += "'{0}': '{1}',\n".format(host, hostmap[host])
    for mp in mplist:
        nodestr += "'{0}',\n".format(mp)

    scriptdir = os.path.dirname(__file__)

    with open('{0}/bootstrap.py.tmpl'.format(scriptdir), 'r') as f:
        script = f.read().replace("$$NOAIP$$", noaip).replace("$$HOSTS$$", hoststr)
    with open("/tmp/{0}.py".format(args.stackname), 'w') as f:
        f.write(script)

    sys.stdout.write("Waiting for NOA MMI to become ready...")
    sys.stdout.flush()

    r = mmirequests.checkAvailable(noafloatingip)
    while r.status_code != 200:
        time.sleep(10)
        sys.stdout.write('.')
        sys.stdout.flush()

        r = mmirequests.checkAvailable(noafloatingip)
    print "up!"

    sshtools.putFile(noafloatingip, "{0}/soapwait.php".format(scriptdir), "/tmp/soapwait.php", "admusr", args.keyfile)
    sshtools.runCommand(noafloatingip, "php /tmp/soapwait.php", "admusr", args.keyfile, printoutput=True)

    print "creating bulk configuraton XML..."
    configureTopology(noafloatingip, topologyInfo, args.stackname)

    print "push ssh key to the NOA..."
    sshtools.putFile(noafloatingip, args.keyfile, "/home/admusr/.ssh/sshkey.pem", "admusr", args.keyfile)
    sshtools.runCommand(noafloatingip, "chmod 600 /home/admusr/.ssh/sshkey.pem", "admusr", args.keyfile, printoutput = True)

    print "initiate bootstrap..."
    sshtools.putFile(noafloatingip, "/tmp/{0}.py".format(args.stackname), "/tmp/bootstrap.py", "admusr", args.keyfile)
    sshtools.runCommand(noafloatingip, "/usr/bin/python /tmp/bootstrap.py", "admusr", args.keyfile, printoutput = True)

    os.unlink("/tmp/{0}.xml".format(args.stackname))
    os.unlink("/tmp/{0}.py".format(args.stackname))

    # Wait for everything to come up
    print "wait for all servers to configure themselves and begin replication..."

    url = "https://{0}/mmi/alexa/v1.0/topo/servers/status".format(noafloatingip)

    # Actually send the configurator request
    ret = {}
    for host in hostmap:
        ret[host] = False

    elapsed = 0
    while (elapsed < 600):

        try:
            resp = mmirequests.get(url)
            r = resp.json()
            for server in r['data']:
                hostname = server['hostname']
                if (not ret[hostname]):
                    print "{0} is now up!".format(hostname)
                ret[hostname] = True

            done = all(up for up in ret.values())
            if done:
                break
            else:
                elapsed += 1
        except Exception as ex:
            #print "{0}: {1}".format(url, ex)
            print "no response from MMI, sleeping..."

        time.sleep(1)

    min, sec = divmod(elapsed, 60)

    for server in ret:
        if not ret[server]:
            print "Server {0} never came up!".format(server)

    if done:
        print "Finished in {0}:{1:02d}!".format(min,sec)
    else:
        print "Timed out after {0}:{1:02d}!".format(min,sec)

    print "Enabling application!"

    for server in ret:
        url = "https://{0}/mmi/alexa/v1.0/topo/servers/{1}/appl".format(noafloatingip, server)
        if ret[server]:
            print "Enabling application on {0}...".format(server)
            data = json.dumps({'applState': 'Enabled'})
            resp = mmirequests.put(url, data=data)
        else:
            print "Server {0} never came up... Not going to enable the application.".format(server)

    #TODO: Application configuration hooks should be loaded and run here!

    print "Complete!"
    print "NOA is accessible at https://{0}/".format(noafloatingip)
    print "SOA is accessible at https://{0}".format(soafloatingip)

if __name__ == "__main__":
    configure()

