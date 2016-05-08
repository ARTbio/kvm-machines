#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: manage_maas_nodes
short_description: Manage MaaS nodes.
requirements:
  - "python >= 2.6"
  - "maasclient >= 0.4.1"
authors:
  - Marius van den Beek (@mvdbeek)
'''

import argparse
import json
try:
    from maasclient.auth import MaasAuth
    from maasclient import MaasClient
    maasclient_imported = True
except ImportError:
    maasclient_imported = False


def request_handling(func):

    def report_request_status(r):
        if not r:
            return None
        if r.status_code != 200:
            response = r.text
            raise Exception("Request failed with Status Code %d, \n %s" % (r.status_code, response))
        else:
            return json.loads(r.text)

    def inner(*args, **kwargs):
        return report_request_status(func(*args, **kwargs))

    return inner


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", action='store', required=True)
    parser.add_argument("--api_url", action='store', required=True)
    parser.add_argument("--mac_address", action='store', type=str.lower, required=True)
    parser.add_argument("--name", action='store')
    parser.add_argument("--power_type", action='store', choices = ["virsh", "etherwake"])
    parser.add_argument("--power_address", action='store')
    return parser.parse_args()


class MaasNodeConnection(object):

    def __init__(self, module):
        self.api_url = module.params["api_url"]
        self.api_key = module.params["api_key"]
        self.check_mode = module.check_mode
        self.mac_address = module.params["mac_address"]
        self.mac_address = self.mac_address.lower()
        self.name = module.params["name"]
        self.power_type = module.params["power_type"]
        self.power_address = module.params["power_address"]
        self.auth = self.authenticate()
        self.client = self.get_client()
        self.nodes = self.client.nodes
        self.system_id = self.get_system_id()

    def authenticate(self):
        return MaasAuth(api_url=self.api_url, api_key=self.api_key)

    def get_client(self):
        return MaasClient(self.auth)

    def get_system_id(self):
        for node in self.nodes:
            for interface in node["interface_set"]:
                if interface["mac_address"] == self.mac_address:
                    self.node = node
                    return node["system_id"]
        raise Exception("Mac address not found in node list")


class MaasNodeOperation(MaasNodeConnection):

    def __init__(self, module):
        super(MaasNodeOperation, self).__init__(module)
        self.api_path = "/nodes/" + self.system_id + "/"
        self.current_hostname = self.node["hostname"]
        self.current_power_parameters = self.get_power_parameters()
        self.current_power_type =  self.node["power_type"]
        self.changed = False
        self.set_hostname()
        self.set_power_type()

    def put(self, params):
        return self.client.put(url=self.api_path, params=params)

    def get(self, params):
        return self.client.get(url=self.api_path, params=params)

    @request_handling
    def get_power_parameters(self):
        params = dict(op="power_parameters")
        return self.get(params=params)

    def set_power_type(self):
        if self.power_type != self.current_power_type:
            self.changed = True
        if self.power_type == "virsh":
            return self.set_power_type_virsh()
        elif self.power_type == "etherwake":
            return self.set_power_type_etherwake()
        else:
            raise Exception("Power type %s not implemented" % self.power_type)

    @request_handling
    def set_power_type_virsh(self):
        params = dict(power_type=self.power_type,
                      power_parameters_power_address=self.power_address,
                      power_parameters_power_id=self.name)
        if self.current_power_parameters["power_address"] == self.power_address and self.current_power_parameters["power_address"] == self.power_address:
            return None
        self.changed = True
        if self.check_mode:
            return None
        return self.put(params=params)

    @request_handling
    def set_power_type_etherwake(self):
        params = dict(power_type=self.power_type,
                      power_parameters_mac_address=self.mac_address)
        if self.current_power_parameters["mac_address"] == self.mac_address:
            return None
        self.changed = True
        if self.check_mode:
            return None
        return self.put(params=params)

    @request_handling
    def set_hostname(self):
        params = dict(hostname = self.name + ".maas")
        if self.current_hostname == params["hostname"]:
            return None
        self.changed = True
        if self.check_mode:
            return None
        return self.put(params=params)

# ===========================================

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name=dict(required=True, type='str'),
            api_key=dict(default=None, type='str', no_log=True, required=True),
            api_url=dict(default=None, type='str', required=True),
            mac_address=dict(default=None, type='str', required=True),
            power_type=dict(default=None, type='str', required=True),
            power_address=dict(default=None, type='str', required=True),
        ),
        supports_check_mode=True
    )

    if not maasclient_imported:
         module.fail_json(msg="maasclient>=0.4.1 could not be imported.")
    try:
        mm = MaasNodeOperation(module)
    except Exception as e:
        module.fail_json(msg=e)

    result = {}
    result['changed'] = mm.changed
    result["name"] = mm.name
    module.exit_json(**result)

#if __name__ == "__main__":
#    main()
#    #args = get_args()
#    #op = MaasNodeOperation(args)
#    #print op.changed

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
