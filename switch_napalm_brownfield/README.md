# Switch Napalm Brownfield

Due to license restriction this example will not contain all the jinja2 (e.g. switch base configuration templates) that are used by the playbooks. But it should be easy to insert the missing templates. All parts that are important for the implementation are included.

## Fabric centric Data-Model

In `./vars` directory the fabric centric data is defined. This data is validated via playbooks:

* valid_vlan_db.yml
* valid_uplinks_db.yml

To transform the fabric specific data into device specific datamodel the following playbook is used.

* gen_device_specific_vars_from_fabric.yml

The device specific client-port datamodel is located in `host_vars` in file `conf_client_ports.yml`

## Set Managed Configuration (Cisco IOS)

The device configuration can be set with the playbook `set_managed_configuratiom.yml`.

The ansible-napalm module `napalm_install_config` is used to update the device configuration.

### Check device configuration changes

To list the configuration changes that will be applied to the device without changing the device configuration use tist command:

```yml
ansible-playbook -i inv_production --limit R01 set_managed_configuration.yml
```

### Apply device configuration changes

To apply the configuration changes to the device add the cli parameter `-e do_commit=1` to the playbook command:

```yml
ansible-playbook -i inv_production --limit R01 set_managed_configuration.yml -e do_commit=1
```

### Define Managed-Configuration Part

The managed part of the device configuration will be defined by providing it as a file (e.g. last device backup) or reading the device's running config and remove all parts that will be managed-configuration.

* Provide the filename of the device configuration in variable `src_config_filename`.
* Read the current running-configuration when `src_config_filename == ""`

The maneged-parts are specified in the list `delete_section_regex`. It contains the regexp search strings to remove the selected configuration sections out of the device config. This removed sections will than be replaced by generating the managed config from datamodel.

```yml
---
#
# file: gen_managed_configuration.yml
#
- hosts: switches
  become: false
  gather_facts: false

  vars:
    # Switch running configuration backup file. if empty the devic's running config wil be used
    src_config_filename: ""

    # Filename of Generated configuration file to replace running-config on switch
    managed_config_dest: "{{ config_dir }}/{{ inventory_hostname }}_managed_configuration.{{ ansible_network_os }}"

    # Generated configuration file to replace running config on switch
    unmanaged_config_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_0001_unmanaged_configuration.{{ ansible_network_os }}"

    # Regex to remove managed configuration sections from current switch configuration
    delete_section_regex:
      - ^Building\s+configuration.*$$
      - ^Current\s+configuration.*$$
      - ^Load\s+for\s+five\s+secs.*$$
      - ^Time\s+source\s+is\s+NTP.*$$
      - ^vlan\s+\d*$$
      - ^ip access-list\s+standard\s+emergency-access$$
      - "^end$$"
      # - ^interface\s+Vlan\d*$$
      # - ^spanning-tree\s+.*$$
      # - ^snmp-server\s+.*$$
      # - ^radius-server\s+.*$$
      # - ^radius\s+server\s+.*$$
      # - ^clock\s+.*$$
      # - ^crypto\s+.*$$

  tasks:

```

The following templates are used to handle ios configuration-sections. A configuration section in an IOS configuration will start with a headerline starting directly at line begin. All the config lines that are part of this section will be intended with a blank.

e.g.:

```text
vlan 12
 name CLIENT-IT
!
```

**Parameters**:

**`src_config:`** current configuration data. The playbook will read in the newly created config after it is modified via a template so consecutive modifications are possible.
**`del_section_regex:`** is the regular expression to find the header of a configuration section.

* `config_section_extractor.j2` extracts the configuration section specified in `del_section_regex` out of `src_config`. This will not modify `src_config`.

```jinja
{% set ns = namespace(is_in_block = false) %}
{% for line in src_config.split('\n') %}
{%   if ns.is_in_block %}
{%     if (line ~ 'x')[0] != ' '%}
{%       if line != '!' %}
{%         set ns.is_in_block = false %}
{%       endif %}
{%     endif %}
{%   endif %}
{%   set found=line | regex_search(del_section_regex) %}
{%   if found %}
{%     set ns.is_in_block = true %}
{%   endif %}
{%   if ns.is_in_block %}
{{ line }}
{%   endif %}
{% endfor %}

```

* `config_section_remover.j2` deletes the configuration section specified in `del_section_regex` out of `src_config`.

```jinja
{% set ns = namespace(is_in_block = false) %}
{% for line in src_config.split('\n') %}
{%   if ns.is_in_block %}
{%     if (line ~ 'x')[0] != ' '%}
{%       if line != '!' %}
{%         set ns.is_in_block = false %}
{%       endif %}
{%     endif %}
{%   endif %}
{%   set found=line | regex_search(del_section_regex) %}
{%   if found %}
{%     set ns.is_in_block = true %}
{%   endif %}
{%   if not ns.is_in_block %}
{{ line }}
{%   endif %}
{% endfor %}
```

### Cisco IOS Banner Configuration Handling

The Cisco Banner configuration needs to be treated different because the `show run` ouput is using the two chars `^C` as text delimiter while it needs the single ASCII char "\x03" that represents the [ctrl]-[c] character to update the banner text from the configuration file.

The code snippet below shows the handling of the different banners. In this example the only managed banner is `banner motd`. The parameter `remove_only` will not preserve the configuration. The other banner data is extracted from configuration and will be preserved.

```yml
- name: Extract all IOS-Banners and replace "^C" with chr(0x03)
      include_tasks: "{{ include_dir }}/inc_config_section_ios_banner_handler.yml"
      vars:
        dest_filename_part: "{{ 9000 + my_index|int }}_banner_{{ item }}"
        template_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_{{dest_filename_part}}.{{ ansible_network_os }}"
        banner_name: "{{ item }}"
        remove_only: "{{ true if item in ['motd'] else false }}"
      loop:
        - motd
        - login
        - exec
        - incoming
        - slip-ppp
      loop_control:
        index_var: my_index
      delegate_to: localhost
```

For banner management the templates are:

* `config_section_ios_banner_extractor.j2`

```jinja
{% set ns = namespace(is_in_block = false) %}
{% set ns.searchfor = '^banner\s+' ~ banner_name ~ '\s+\^C$$' %}
{% set ns.is_first = true %}
{% for line in src_config.split('\n') %}
{%   set found=line | regex_search( ns.searchfor ) %}
{%   if found and ns.is_first %}
{%     set ns.is_in_block = true %}
{%     set ns.is_first = false %}
banner {{ banner_name ~ " \x03" }}
{%   elif ns.is_in_block %}
{%     if line == "^C" %}
{%       set ns.is_in_block = false %}
{{       "\x03" }}
{%     else %}
{{       line }}
{%     endif %}
{%   endif %}
{% endfor %}
```

* `config_section_ios_banner_remover.j2`

```jinja
{% set ns = namespace(is_in_block = false) %}
{% set ns.searchfor = '^banner\s+' ~ banner_name ~ '\s+\^C$$' %}
{% for line in src_config.split('\n') %}
{%   set found=line | regex_search(ns.searchfor) %}
{%   if found %}
{%     set ns.is_in_block = true %}
{%   endif %}
{%   if ns.is_in_block %}
{%     if line == '^C' %}
{%       set ns.is_in_block = false %}
{%     endif %}
{%   else %}
{{     line }}
{%   endif %}
{% endfor %}
```

## Generate Managed configuration

This plays generating the managed configurations:

**important:** one always have to remove the `end` marker `- "^end$$"` because it's used to detect the end of configuration.

```yaml
#######################################################################
    # Generate managed configuration parts from datamodel
    #######################################################################

    - name: Generate VLAN Device-VLAN configuration
      include_tasks: "{{ include_dir }}/inc_template.yml"
      vars:
        dest_filename_part: "0010_vlan_configuration"
        template_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_{{dest_filename_part}}.{{ ansible_network_os }}"
        template_name: "config_vlans.j2"
      delegate_to: localhost

    - name: Generate Client Ports Configuration
      include_tasks: "{{ include_dir }}/inc_template.yml"
      vars:
        dest_filename_part: "0800_client_ports_configuration"
        template_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_{{dest_filename_part}}.{{ ansible_network_os }}"
        template_name: "config_client_interfaces.j2"
      delegate_to: localhost

    - name: Generate Emergency Access List
      include_tasks: "{{ include_dir }}/inc_template.yml"
      vars:
        dest_filename_part: "0100_acl_emergency_access_configuration"
        template_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_{{dest_filename_part}}.{{ ansible_network_os }}"
        template_name: "config_acl_emergency_access.j2"
      delegate_to: localhost

    - name: Generate banner motd
      include_tasks: "{{ include_dir }}/inc_template.yml"
      vars:
        display_core: "{{ '( --- CORE-SWITCH --- )' if is_default_gateway is defined and is_default_gateway == true else '' }}"
        dest_filename_part: "9010_banner_client_ports_configuration"
        template_dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_{{dest_filename_part}}.{{ ansible_network_os }}"
        template_name: "config_ios_banner_motd.j2"
      delegate_to: localhost


    - name: Write end marker
      copy:
        content: "end"
        dest: "{{ host_tmpdir }}/{{ inventory_hostname }}_9999_end.{{ ansible_network_os }}"
      delegate_to: localhost

```

To put it all together, the configuration is combined with Ansible module `assemble`. Here the regexp is used as a constraint that only `*.ios` files are assembled into the configuration file specified in `managed_config_dest`

```yaml
    - name: Assemble configuration
      assemble:
        src: "{{ host_tmpdir }}"
        dest: "{{ managed_config_dest }}"
        regexp: "^.*\\.{{ ansible_network_os }}$$"
      delegate_to: localhost
```

## Commit or Show Configuration Difference

The vatiable `do_commit` determines if the configuration is stored to the device or only the config difference is listed.

```yaml

    - name: Set Configuration - Check-Mode if do_commit is not defined
      napalm_install_config:
        config_file: "{{ managed_config_dest }}"
        commit_changes: "{{ do_commit is defined}}"
        replace_config: true
        get_diffs: true
        diff_file: "{{ managed_config_dest }}.diff"
        hostname: "{{ ansible_host  }}"
        username: "{{ ansible_user }}"
        dev_os: "{{ ansible_network_os }}"
        password: "{{ ansible_ssh_pass }}"
        timeout: 120
      register: result
      tags: [print_action]


    - name: Display Commit Message
      debug:
        msg: "Generated: {{ managed_config_dest }}\nTo apply the changes to the device use commandline parameter -e do_commit=1"
      when:
        - do_commit is not defined
      run_once: true
      delegate_to: localhost
      tags: [print_action]

```

## Requirements

ansible-napalm module will be used.
see documentation: <https://napalm.readthedocs.io/en/latest/index.html>

Tested on:
    ansible                    2.7.4
    napalm                     2.3.2
    napalm-ansible             0.10.0
    yamllint                   1.12.1

    Catalyst C6824-X-LE-40G  15.4(1)SY4
    Catalyst C9300-48P       16.06.04a

## Compliance Reports Framework

Updated version in ./compliance

Bash scripts to start report generation from cron is included in scripts directory.
