import atexit
from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect
from ansible.module_utils.basic import *
from pyVim.connect import SmartConnect
import ssl

s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
s.verify_mode = ssl.CERT_NONE

def get_all_objects(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj

def find_dvs_by_name(content, vds_name):
    vdSwitches = get_all_objects(content, [vim.dvs.VmwareDistributedVirtualSwitch])
    for vds in vdSwitches:
        if vds_name == vds.name:
            return vds
    return None

def find_vdspg_by_vlanid(vdSwitch, vlanid):
    portgroups = vdSwitch.portgroup
    for pg in portgroups:
        try:
           if pg.config.defaultPortConfig.vlan.vlanId == vlanid:
              return pg
        except:
           pass
    return None


def main():
    fields = {
        "vcenter_host": {"required": True, "type": "str"},
        "vcenter_user": {"required": True, "type": "str"},
        "vcenter_pass": {"required": True, "type": "str"},
        "dvs_name": {"required": True, "type": "str"},
        "pg_vlanid": {"required": True, "type": "int"},
        }

    try:
        module = AnsibleModule(argument_spec=fields)
        si = None
        data = module.params
        try:
            si = connect.Connect(data['vcenter_host'], 443, data['vcenter_user'], data['vcenter_pass'], version="vim.version.version8", sslContext=s)
        except IOError, e:
            pass
            atexit.register(Disconnect, si)

        content = si.RetrieveContent()

        dvs =  find_dvs_by_name(content, data['dvs_name'])
        pg = find_vdspg_by_vlanid(dvs, data['pg_vlanid'])

        response = {"name": pg.name, "vlan": pg.config.defaultPortConfig.vlan.vlanId}
        module.exit_json(changed=False, meta=response)
    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        return 1
    except Exception, e:
        print "Caught exception: %s" % str(e)
        return 1

main()
