# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: client_intf_str
short_description: This filter allows to get Cisco IOS compatible interface name and number form short name e.g. "gi1/0/10" -> "GigabiEthernet1/0/10"

version_added: "2.7"
description:
  This filter is parsing a case insensitive string and returning the apropriate
  interface name. The first two chars are used to determine the interface name.

  String start with:
    "et" - eth
    "Fa" - FastEthernet
    "Gi" - GigabitEthernet
    "Te" - TenGigabitEthernet
    "Tw" - TwentyfiveGigabitEthernet
    "Fo" - FortyGigabitEthernet
    "Hu" - HundredGigabitEthernet
    "Lo" - Loopback
    "Ma" - Management
    "Po" - ""      # only port number will be set

For e.g.:

  - set_fact:
      - intf: "{{ 'gi1/0/4' | client_intf_str }}

  will return the dictionary intf:

  intf:
    name: "GigabitEthernet"
    number: "1/0/4"

'''

from ansible.errors import AnsibleFilterError


def parse_client_intf_str(str):
  id = str[:2].lower()
  if id == u'fa':
    _interface = u'FastEthernet'
  elif id == u'gi':
    _interface = u'GigabitEthernet'
  elif id == u'te':
    _interface = u'TenGigabitEthernet'
  elif id == u'tw':
    _interface = u'TwentyfiveGigabitEthernet'
  elif id == u'fo':
    _interface = u'FortyGigabitEthernet'
  elif id == u'hu':
    _interface = u'HundredGigabitEthernet'
  elif id == u'ma':
    _interface = u'Management'
  elif id == u'lo':
    _interface = u'Loopback'
  elif id == u'et':
    _interface = u'eth'
  elif id == u'po':
    _interface = u''
  else:
    raise AnsibleFilterError('client_intf_str: unknown category: %s' % id)
  return {'name': _interface, 'number': str[2:]}


# ---- Ansible filters ----
class FilterModule(object):
    def filters(self):
        return {
            'client_intf_str': parse_client_intf_str
        }
