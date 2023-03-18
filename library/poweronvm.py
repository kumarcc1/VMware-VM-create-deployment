#!/usr/bin/env python

from __future__ import print_function

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl

import argparse
import atexit
import getpass
import sys
import ssl

from ansible.module_utils.basic import *

s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
s.verify_mode = ssl.CERT_NONE

def WaitForTasks(tasks, si):

   pc = si.content.propertyCollector

   taskList = [str(task) for task in tasks]

   # Create filter
   objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                                                            for task in tasks]
   propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                         pathSet=[], all=True)
   filterSpec = vmodl.query.PropertyCollector.FilterSpec()
   filterSpec.objectSet = objSpecs
   filterSpec.propSet = [propSpec]
   filter = pc.CreateFilter(filterSpec, True)

   try:
      version, state = None, None

      # Loop looking for updates till the state moves to a completed state.
      while len(taskList):
         update = pc.WaitForUpdates(version)
         for filterSet in update.filterSet:
            for objSet in filterSet.objectSet:
               task = objSet.obj
               for change in objSet.changeSet:
                  if change.name == 'info':
                     state = change.val.state
                  elif change.name == 'info.state':
                     state = change.val
                  else:
                     continue

                  if not str(task) in taskList:
                     continue

                  if state == vim.TaskInfo.State.success:
                     # Remove task from taskList
                     taskList.remove(str(task))
                  elif state == vim.TaskInfo.State.error:
                     raise task.info.error
         # Move to next version
         version = update.version
   finally:
      if filter:
         filter.Destroy()


def main():
    fields = {
            "vcenter_host": {"required": True, "type": "str"},
            "vcenter_user": {"required": True, "type": "str"},
            "vcenter_pass": {"required": True, "type": "str"},
            "vm_name": {"required": True, "type": "str"},
            }

    module = AnsibleModule(argument_spec=fields)
    data = module.params
    vmnames = data['vm_name']

    si = SmartConnect(host=data['vcenter_host'],
                      user=data['vcenter_user'],
                      pwd=data['vcenter_pass'],
                      port=443,
                      sslContext=s)

    atexit.register(Disconnect, si)
    content = si.content
    objView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
    vmList = objView.view
    objView.Destroy()
    tasks = [vm.PowerOn() for vm in vmList if vm.name in vmnames]
    WaitForTasks(tasks, si)
    response = {"name": "Virtual Machine(s) have been powered on successfully"}
    module.exit_json(changed=False, meta=response)

main()
