#!/usr/bin/env python

import argparse
import ipaddress
import math
import os
import sys

from yaml import dump
import yaml


#JTH created flavors func
def genflavors(name, ram, vcpus, disk):
    flavor = {}
    flavor['name'] = name
    flavor[name] = {
            'type': 'OS::Nova::Flavor',
            'properties': {
                'ram':   ram,
                'vcpus': vcpus,
                'disk':  disk
            }
        }

    return flavor[name]


def gennet(name, nename, cidr, routed=True ,shared=True):
    net = {}
    net_prop = {}
    meta = {}
    subnet = {}
    interface = None

    resourceName = "{0}_{1}".format(nename, name)

    paramName = resourceName + "_cidr"

    param = {
        paramName: {
            'type': 'string',
            'label': "{0} {1} Network Address".format(nename, name),
            'default': cidr
        }
    }

    meta['name'] = name
    meta['neName'] = nename
    #JTH to key\ off in stackconfigure
    meta['shared'] = shared
    meta['routed'] = routed

    #JTH added properties to networks 
    # portsecurity off
    net_prop['name'] = name
    net_prop['port_security_enabled'] = False

    net['properties'] = net_prop

    net['type'] = 'OS::Neutron::Net'
    net['metadata'] = meta

    subnet['type'] = 'OS::Neutron::Subnet'

    props = {}
    props['network_id'] = {'get_resource': resourceName}
    props['cidr'] = {'get_param': paramName}

    if routed:
        props['dns_nameservers'] = ['192.168.56.180', '10.75.137.245', '10.75.137.246']
    else:
        props['gateway_ip'] = None
    #JTH
    #if not (routed or shared):
        
    subnet['properties'] = props

    if routed:
        interface = {}
        interface['type'] = "OS::Neutron::RouterInterface"
        props = {}
        props['router_id'] = {'get_resource': 'router'}
        props['subnet'] = {'get_resource': "{0}_subnet".format(resourceName)}

        interface['properties'] = props

    return {
        'name': resourceName,
        'shortname': name,
        'net': net,
        'subnet': subnet,
        'interface': interface,
        'params': param,
        'shared': shared,
    }

def genserver(name, nename, sgname, nets, role, flavor, hwprofile,
              primary = False, haRolePref = None, extra = False,
              user_data = None, image = None):
    instance = {}
    props = {}
    meta  = {}
    ports = {}
    floatingips = {}

    ipname = None

    instance['type'] = "OS::Nova::Server"

#JTH added flavor resource
    props["flavor"] = { "get_resource": flavor } 
   # props["flavor"] = flavor

    if not image:
        image = {"get_param":"image"}

    props["image"] = image

    props["key_name"] = {"get_param": "sshkeypair"}
    props["name"] = {
        'str_replace': {
            'template': '$name-{0}'.format(name),
            'params': {
                '$name': {'get_param': 'OS::stack_name'}
            }
        }
    }

    props['user_data_format'] = "RAW"

    if not user_data:
        user_data = open("{0}/cloudconfig.yaml.tmpl".format(os.path.dirname(__file__))).read()

    props["user_data"] = {
        'str_replace':{
            'template': user_data,
            'params': {
                '$stack': {'get_param': 'OS::stack_name'},
                '$name': name
            }
        }
    }

    meta['neName'] = nename
    meta['sgName'] = sgname
    meta['role']   = role
    meta['extra'] = extra

    meta['hwprofile'] = hwprofile

    if role == "roleNOAMP" and primary:
        meta['noa'] = True
    else:
        meta['noa'] = False

    if haRolePref:
        meta['haRolePref'] = haRolePref


    props['networks'] = []

    meta['portmap'] = {}
    devicenumber = 0

    for net in nets:
        portname = "{0}_{1}_port".format(name, net['name'])

        meta['portmap'][net['shortname']] = "eth{0}".format(devicenumber)
        devicenumber += 1

#JTH add secu groups to xmi port
        #if "XMI" in portname:
        ports[portname] = {
            'type': 'OS::Neutron::Port',
            'properties': {
                'network': {'get_resource': net['name']},
            #    'security_groups': [{ 'get_resource':  'secu_group' }]
            }
        }

        #else:
        #    ports[portname] = {
        #        'type': 'OS::Neutron::Port',
        #        'properties': {
        #            'network': {'get_resource': net['name']}
        #        }
        #    }


        if primary and net['interface']:
            ipname = portname + "_fip"
            floatingips[ipname] = {
                'type': 'OS::Neutron::FloatingIP',
                'depends_on': net['name'] + '_intf',
                'properties': {
                    'floating_network': {'get_param': 'public_network'},
                    'port_id' : {'get_resource': portname}
                }
            }

        props['networks'].append({'port': {'get_resource': portname}})

    instance['properties'] = props
    instance['metadata'] = meta

    return {
        'name': name,
        'instance': instance,
        'ports': ports,
        'floatingips': floatingips,
        'floatingipout': ipname,
    }

def genyaml(input):

#JTH added img,ext_net and key_name to input.yml file
    img =  input['params']['image']
    ext_net = input['params']['public_network']
    #nename = input['params']['nename']
    key_name =  input['params']['ssh_key']

    params = {
        'image': {
            'type': 'string',
            'label': 'Image Name',
            'default': img,
        },
        'public_network': {
            'type': 'string',
            'label': 'Public Network ID',
            'default': ext_net,
        },
        'sshkeypair': {
            'type': 'string',
            'label': 'SSH keypair name',
            'default': key_name,
        }
    }

    paramGroups = [
        {
            'label': 'VM Options',
            'parameters': [ 'image', 'sshkeypair' ]
        }
    ]
    netParams = ['public_network']

    resources = {}
    appworks = {
        'networkelements': [],
        'servergroups': []
    }

    flavor = {}
    image = {}
    nets = {}
    yamlnets = []
    servers = []
    outputs = {}

    nets['NO_NE'] = {}
    nets['GLOBAL'] = {}

    if input['params']['networks']:
      for net in input['params']['networks']:
            nets['NO_NE'][net['name']] = gennet(net['name'], "NO_NE", net['cidr'], net['routed'], net['shared'])
            yamlnets.append(nets['NO_NE'][net['name']])

    for net in input['params']['globalnetworks']:
        nets['GLOBAL'][net['name']] = gennet(net['name'], "GLOBAL", net['cidr'], net['routed'], net['shared'])
        yamlnets.append(nets['GLOBAL'][net['name']])

    resources['router'] = {
        'type': 'OS::Neutron::Router',
        'properties':{
            'external_gateway_info': {
                'network': {'get_param': 'public_network'}
            }
        }
    }

    # NO Network Element stuff. This will always be here.
    nofunction = input['params']['noampfunction']

    appworks['networkelements'].append({'name': 'NO_NE'})
    appworks['servergroups'].append({'name': 'NO_SG',
                                     'level':'A',
                                     'parentSgName':'NONE',
                                     'functionName': nofunction,
                                     'numWanRepConn': 1})

    appworks['services'] = input['params']['services']

    servernets = []
    for net in input['params']['interfaces']:
        n = nets['NO_NE'].get(net,nets['GLOBAL'].get(net, None))
        servernets.append(n)

#JTH added secu group resource

    resources['secu_group'] = {
      'type': 'OS::Neutron::SecurityGroup',
      'properties': {
        'name': 'custom',
        'description': 'Ping SSH Web',
        'rules': [{
          'protocol': 'tcp',
          'remote_ip_prefix': '0.0.0.0/0',
          'port_range_min': '1',
          'port_range_max': '65535'
          }, {
          'protocol': 'icmp',
          'remote_ip_prefix': '0.0.0.0/0'
          }, {
          'remote_ip_prefix': '0.0.0.0/0',
          'port_range_min': '22',
          'port_range_max': '22',
          'protocol': 'tcp'
          }, {
          'port_range_min': '443',
          'port_range_max': '443',
          'remote_ip_prefix': '0.0.0.0/0',
          'protocol': 'tcp'
          }, {
          'port_range_min': '80',
          'port_range_max': '80',
          'remote_ip_prefix': '0.0.0.0/0',
          'protocol': 'tcp'
          }]
       }
   }

    for flav in input['params']['flavors']:
              resources[flav['name']] = genflavors(**flav)

    noampflavor = input['params']['noampflavor']
    noampprofile = input['params']['noampprofile']

    noa = genserver("noa", "NO_NE", "NO_SG", servernets, "roleNOAMP", noampflavor, noampprofile, primary = True)
    noa['instance']['metadata']['appworks'] = appworks

    nob = genserver("nob", "NO_NE", "NO_SG", servernets, "roleNOAMP", noampflavor, noampprofile, haRolePref = "SPARE")
    servers += [noa, nob]

    nenum = 1
    for ne in input['params']['networkelements']:
        mpnum = 1
        nename = "SO_NE{0}".format(nenum)
        nets[nename] = {}
        appworks['networkelements'].append({'name': nename})

        for net in ne['networks']:
            #JTH if shared networks 
            if nets['NO_NE'][net['name']]['shared']:
               nename = "NO_NE"
                
            nets[nename][net['name']] = gennet(net['name'], nename, net['cidr'], net['routed'], net['shared'])
            yamlnets.append(nets[nename][net['name']])
                    

        servernets = []
        for net in ne['interfaces']:
            n = nets[nename].get(net,nets['GLOBAL'].get(net, None))
            servernets.append(n)

        sosgname = "SO_SG{0}".format(nenum)
        appworks['servergroups'].append({'name': sosgname,
                                         'level':'B',
                                         'parentSgName':'NO_SG',
                                         'functionName': ne['soamfunction'],
                                         'numWanRepConn': 1})

        #JTH reset nename
        if "SO_NE" not in nename:
            so_nename = "SO_NE{0}".format(nenum)

        soa = genserver("soa{0}".format(nenum), so_nename, sosgname, servernets, "roleSOAM", ne['soamflavor'], ne['soamprofile'], primary = True)
        sob = genserver("sob{0}".format(nenum), so_nename, sosgname, servernets, "roleSOAM", ne['soamflavor'], ne['soamprofile'], haRolePref = "SPARE")
        servers += [soa, sob]

        # mpservergroups
        sgnum = 1
        for sg in ne['mpservergroups']:
            mpsgname = "SO{0}MP_SG{1}".format(nenum, sgnum)
            appworks['servergroups'].append({'name': mpsgname,
                                             'level':'C',
                                             'parentSgName': sosgname,
                                             'functionName': sg['function'],
                                             'numWanRepConn': 1})

            for rawmpnum in range(0, sg['mpcount']):
                servernets = []
                for net in sg['interfaces']:
                    n = nets[nename].get(net,nets['GLOBAL'].get(net, None))
                    servernets.append(n)

                mp = genserver("so{0}mp{1}".format(nenum, mpnum), so_nename, mpsgname, servernets, "roleMP", sg['mpflavor'], sg['mpprofile'])
                servers += [mp]
                mpnum += 1
            sgnum += 1

        # ipfegroups
        mpnum = 1
        sgnum = 1
        if ne['ipfeservergroups']:
            for sg in ne['ipfeservergroups']:
                ipfesgname = "SO{0}IPFE_SG{1}".format(nenum, sgnum)
                appworks['servergroups'].append({'name': ipfesgname,
                                                 'level':'C',
                                                 'parentSgName': sosgname,
                                                 'functionName': sg['function'],
                                                 'numWanRepConn': 1})

                for rawmpnum in range(0, sg['ipfecount']):
                    servernets = []
                    for net in sg['interfaces']:
                        n = nets[nename].get(net,nets['GLOBAL'].get(net, None))
                        servernets.append(n)

                    ipfe = genserver("so{0}ipfe{1}".format(nenum, mpnum), so_nename, ipfesgname, servernets, "roleMP", sg['ipfeflavor'], sg['ipfeprofile'])
                    servers += [ipfe]
                    mpnum += 1
                sgnum += 1
    nenum += 1

     # Add any extra servers
    for server in input['extras']:
        servernets = []
        for net in server['interfaces']:
            n = nets[net['nename']][net['network']]
            servernets.append(n)

        s = genserver(server['name'],"NONE","NONE",servernets,"NONE",server['flavor'], None, extra = True, user_data = server['user-data'], image = server['image'])
        servers += [s]

    netOptions = []
# put it all together!
    for net in yamlnets:
        name = net['name']
        resources[name] = net['net']
        resources[name+"_subnet"] = net['subnet']
        if net['interface']:
            resources[name+"_intf"] = net['interface']
        for key in net['params']:
            params[key] = net['params'][key]

            #JTH added to so - label: Network Options is unique if using same resource names
            if key not in netParams:
                #print "KEY...{0}".format(key)
                netOptions.append(key)
    
            netParams.append(key)

    for server in servers:
        name = server['name']
        resources[name] = server['instance']
        for port in server['ports']:
            resources[port] = server['ports'][port]
        for fip in server['floatingips']:
            resources[fip] = server['floatingips'][fip]

        floatingipout = server['floatingipout']
        if floatingipout:
            outputs['floatingip_{0}'.format(name)] = {
                "description": "The floating IP used to access '{0}'.".format(name),
                "value": {
                    "get_attr": [floatingipout, 'floating_ip_address']
                }
            }

    paramGroups.append({
        'label': 'Network Options',
        'parameters': netOptions
    })

    doc = {"heat_template_version": "2015-04-30", "parameter_groups": paramGroups,
           "parameters": params, "resources": resources, "outputs": outputs}

    return dump(doc, default_flow_style=False)

def generate():
    parser = argparse.ArgumentParser(description="Generate a HOT template.")
    parser.add_argument("input", help="Input YAML specification", type=str)
    args = parser.parse_args()

    inputdata = yaml.load(open(args.input).read())

    print genyaml(inputdata)

if __name__ == "__main__":
    generate()
