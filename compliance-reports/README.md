# Compliance Repots

Compliance Reports for Network infrastructure using Ansible

This playbook contains a framework to generate a composite report of all executed checks. 

## Requirements

ansible-napalm module will be used. 
see documentation: https://napalm.readthedocs.io/en/latest/index.html

Tested on:
    ansible                    2.6.4  
    napalm                     2.3.2
    napalm-ansible             0.10.0

    Catalyst C6824-X-LE-40G  15.4(1)SY4
    Catalyst C9300-48P       16.06.04
            

## Framework description

The framework is started by executing the playbook 'run_all_checks.yml'.

The checks that should be executed are defined with the variable 'checks_to_run'.
There are two pseudo checks 'report_header' and 'report_footer' that generates the
header and footer of the composite report. These should not be removed.

  vars:
    checks_to_run:
      - report_header
      - check_available_ports
      - check_ntp_sync
      - check_os_version
      - report_footer
    report_dir: "{{playbook_dir}}/../reports"

The framwork will cleanup previously generated data and execute each check.
The report data will be stored for each check in a separat directory. The
file naming convention ensures that the generated files (header, data, footer)
will be assembled in order.


### Directory Structure
Every check uses the same directory layout and will be executed by calling 
'run_check.yml'. For every check, a directory named like defined in 'checks_to_run'
variable must be created under the 'checks' sundirectory.

In there a subdirectory depending on the switch-operating-system allows to
use different jinja2 templates for report generation. The content of
{{ ansible_network_os }} is used for that.

In there a subdirectory for each output format is expected where the templates
to generate the report will be stored.

├── compliance
│   ├── checks
│   │   ├── check_ntp_sync
│   │   │   ├── ios
│   │   │   │   ├── html
│   │   │   │   │   ├── data.j2
│   │   │   │   │   ├── footer.j2
│   │   │   │   │   └── header.j2
│   │   │   │   └── txt
│   │   │   │       ├── data.j2
│   │   │   │       ├── footer.j2
│   │   │   │       └── header.j2
│   │   │   └── run_check.yml
│   │   ├── check_os_version


## run_check.yml

run_check.yml will be called to generate a particular report.

### Playbook run_check.yml
This is usually just a standard playbook that uses the defined 
filenames to generate the report data. Header ans Footer are 
executed only once.

        ---
        # HEADER
        - name: Generate Header
        template:
            src: "{{ header_template_name }}"
            dest: "{{ header_output_name }}"
        run_once: yes
        delegate_to: localhost

        # DATA
        - name: Generate output for current host
        template:
            src: "{{ data_template_name }}"
            dest: "{{ data_output_name }}"
        delegate_to: localhost

        # FOOTER
        - name: Generate footer Output
        template:
            src: "{{ footer_template_name }}"
            dest: "{{ footer_output_name }}"
        run_once: yes
        delegate_to: localhost

### Defined Variables for run_check.yml

It's important to use the defined names in the playbook because in
this way the run_check.yml can be standardized.

    Template names:
    ---------------
        header_template_name: "{{ playbook_dir }}/checks/{{ current_check }}/{{ ansible_network_os if (current_check !=  'report_header' and current_check != 'report_footer') else '' }}/{{ report_fmt }}/header.j2"
        
        data_template_name: "{{ playbook_dir }}/checks/{{ current_check }}/{{ ansible_network_os if (current_check != 'report_header' and current_check !=  'report_footer') else '' }}/{{ report_fmt }}/data.j2"
    
        footer_template_name: "{{ playbook_dir }}/checks/{{ current_check }}/{{ ansible_network_os if (current_check != 'report_header' and current_check != 'report_footer') else '' }}/{{ report_fmt }}/footer.j2"

    Output Names:
    -------------
        header_output_name: "{{ report_dir }}/{{ current_check }}/2_{{ current_check }}.{{report_fmt}}"

        data_output_name: "{{ report_dir }}/{{ current_check }}/5_{{ inventory_hostname }}_{{ current_check }}.{{report_fmt}}"
    
        footer_output_name: "{{ report_dir }}/{{ current_check }}/7_{{ current_check }}.{{report_fmt}}"

    Historical Data:
    ----------------
        To stoe historical data use the directory defined in historical_data_dir

        historical_data_dir: "{{ report_dir }}/data"

## Commandline Parameters

- paramter: rep_fmt   default: html
      this determines which report format should be generated
      use:  ansible-playbook -i hosts.yml compliance/run_all_checks.yml -e rep_fmt=html

## Variables

### group_vars/all.yml

    baseline_switch_data: 
    --------------------
        define certified version for your infrastructure. The ios templates are using the
        values gathered from ios_facts to compare.

            # Baseline Switch Operating Systems
            # Values from ios_facts
            #    "ansible_net_model": "C6824-X-LE-40G",
            #    "ansible_net_version": "15.4(1)SY4",
            #
            baseline_switch_data: [
                { model: "C6824-X-LE-40G", os_version: "15.4(1)SY4" },
                { model: "C9300-48P",      os_version: "16.06.04"   }
            ]

    client_ports_regex: "GigabitEthernet\\d+\\/0\\/\\d+"
    ------------------
        This regex is used to determine which switchports should be counted as
        client switchports on edge-switches

## Example

ansible-playbook -i hosts.yml compliance/run_all_checks.yml

Example .html output
    see: reports/compliance_reports_20180916-123243.html

