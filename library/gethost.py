#!/usr/bin/env python
"""
List Of Hosts in a Cluster
"""
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import atexit
import argparse
import getpass
import ssl
import requests
import random
from ansible.module_utils.basic import *


def get_obj(content, vimtype, name = None):
    return [item for item in content.viewManager.CreateContainerView(
        content.rootFolder, [vimtype], recursive=True).view]

s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
s.verify_mode = ssl.CERT_NONE


def main():
    fields = {
            "vcenter_host": {"required": True, "type": "str"},
            "vcenter_user": {"required": True, "type": "str"},
            "vcenter_pass": {"required": True, "type": "str"},
            "cluster_name": {"required": True, "type": "str"},
            }
    module = AnsibleModule(argument_spec=fields)
    data = module.params
    # connect this thing
    si = SmartConnect(
        host=data['vcenter_host'],
        user=data['vcenter_user'],
        pwd=data['vcenter_pass'],
        port=443,
        sslContext=s)

    # disconnect this thing
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()

    for cluster_obj in get_obj(content, vim.ComputeResource,
            data['cluster_name']):
        if data['cluster_name']:
            if cluster_obj.name == data['cluster_name']:
                hran = cluster_obj.host[int(random.random() * len(cluster_obj.host))].name
                response = {"name": hran}
                module.exit_json(changed=False, meta=response)

        else:
            print cluster_obj.name

# start this thing
if __name__ == "__main__":
    main()
