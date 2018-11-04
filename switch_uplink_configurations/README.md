# Switch Uplink Configurations

This playbooks are intended to generate a configuration file that can be used to initially configure Layer 2 uplinks between network devices.

It´s also possible to define links to devices that are not part of the inventory.

## Requirements

Tested with Ansible 2.6.4

Install filter_plugin `client_intf_str.py`.

## Structure

The uplinks are defined in directory `vars`
There is one level of subdirectories that is used to distinquish between different definitions. E.g. different production sited or tenants.
The available groups are defined in variable `location_groups`.

```yaml
# Will be used to select the vars for a particular group
location_groups:
  - PLANT_A
```

## Defining uplinks

the variable `switch_uplinks` contains the information about all uplinks within a `location_group`.

### Example definition

File: `vars/PLANT_A/uplinks_db.py`

```yaml
---
# switch_uplinks:   used to define all uplinks between network devices.
#
#   channel_linktype:  (required for channel) Link aggregation mode
#                        ["active" <--default | "desirable" | "on"]
#   channel_nr_left:   (required for channel) Port-channel number on left device if uplink_type == channel
#   channel_nr_right:  (required for channel) Port-channel number on right device if uplink_type == channel
#   description:       (optional) else default description will be generated
#   interface_left:    interfaces on left device (must be same count than interfaces_right) [Te | Gi | et | Po]
#   interface_right:   interfaces on right device (must be same count than interfaces_left) [Te | Gi | et | Po]
#   key:               IMPORTANT: NAMING CONVENTION
#                        1.) inventory_hostname of left device - alphabetically smaller than right device
#                                                                this assures that no duplicates are defined
#                        2.) underline character '_'
#                        3.) inventory_hostname of right device
#                        4.) (optional) underline character '_'
#                        5.) (optional) unique identifier to allow multiple connections between devices
#   native_vlan:       (optional - default: switchport_default_vlan_id) vlan for access port or
#                      untagged vlan for channels and trunks.
#                      allowed VLANs are all vlans that are defined for this device
#   root_guard:        (optional) Enable spanning-tree guard root [ true | false <-- default ]
#   uplink_type:       access | trunk | channel <-- default
#
switch_uplinks:
  "AP001_SW002":
    uplink_type: access
    native_vlan: "33"
    interfaces_left:  [Gi1/0/23]
    interfaces_right: [Gi0/1]

  "ROUTER01_SW001":
    uplink_type: channel
    channel_linktype: "desirable"
    channel_nr_left: "1"
    channel_nr_right: "1"
    interfaces_left:  [Te1/1/1, Te2/1/1]
    interfaces_right: [Te1/1/1, Te2/1/1]
  "ROUTER01_SW002_02":
    uplink_type: trunk
    channel_nr_left: "2"
    channel_nr_right: "1"
    interfaces_left:  [Te1/1/2]
    interfaces_right: [Te1/1/1]
  "ROUTER01_FIREWALL01":
    uplink_type: channel
    channel_linktype: "on"
    channel_nr_left: "24"
    channel_nr_right: "1"
    native_vlan: "10"
    root_guard: true
    interfaces_left:  [Gi1/0/24, Gi2/0/24]
    interfaces_right: [et2-1, et2-2]

  "SW001_VMWARE001":
    uplink_type: channel
    channel_linktype: "on"
    channel_nr_left: "3"
    channel_nr_right: "3"
    native_vlan: "20"
    root_guard: true
    interfaces_left:  [Te1/1/3, Te2/1/3]
    interfaces_right: [te1, Te2]

  "SW001_SW002":
    uplink_type: trunk
    interfaces_left:  [Te2/1/2]
    interfaces_right: [te1/1/2]
```
---

## Playbooks

There are two playbooks in here.

### gen_base_uplink_configuration.yml

Is used to generate the initial configuration for a switch.  This will generate as an output all commands needed to define the uplinks during initial device configuration.


### gen_uplink_configuration.yml

Generates the output that may be used to compare to running configuration. Can be used for e.g. with napalm_config module to define the uplink data.

---

## Output Directory

The generated configuration files are stored in `./configs` dir.

---

## Filter-Plugin - client_intf_str

This filter is parsing a case insensitive string and returning the appropriate interface name and number. The first two chars are used to determine the interface name.

```yaml
  String star twith:
    "Fo" - FortyGigabitEthernet
    "Te" - TenGigabitEthernet
    "Gi" - GigabitEthernet
    "et" - eth
    "Po" - ""      # only port number will be set
```

for e.g.:
```yaml
  - set_fact:
      - intf: "{{ 'gi1/0/4' | client_intf_str }}
```
will return the dictionary `intf`:

```yaml
  intf:
    name: "GigabitEthernet"
    number: "1/0/4"
```
