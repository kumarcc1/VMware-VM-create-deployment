#!/usr/bin/env python

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit
import argparse
import getpass
from ansible.module_utils.basic import *
import ssl
import time

s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
s.verify_mode = ssl.CERT_NONE


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def add_disk(vm, si, disk_size, disk_type):
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        unit_number = 1
        for dev in vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    print "we don't support this many disks"
                    return
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        # add disk here
        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        vm.ReconfigVM_Task(spec=spec)


def main():
    fields = {
            "vcenter_host": {"required": True, "type": "str"},
            "vcenter_user": {"required": True, "type": "str"},
            "vcenter_pass": {"required": True, "type": "str"},
            "vm_name": {"required": True, "type": "str"},
            "type": {"required": True, "type": "str"},
            "size": {"required": True, "type": "int"},
            }
    module = AnsibleModule(argument_spec=fields)
    data = module.params
    time.sleep(5)
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
    vm = None
    vm = get_obj(content, [vim.VirtualMachine], data['vm_name'])

    if vm:
        add_disk(vm, si, data['size'], data['type'])
        response = {"name": data['vm_name'],"success": "True"}
    else:
        print "VM not found"
        response = {"name": data['vm_name'],"success": "False"}
    module.exit_json(changed=False, meta=response)

# start this thing
main()

