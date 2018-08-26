jifox.cisco_backup
==================

This rule stores switch (Cisco ios) config backups backup-files to a given backup directory when changes between the last saved configuration are detected. In that case the running-config will also be saved to startup-config on the switch.

Ansible-napalm is used to read the running-config because ios_config module runs into an error (see Ansible Issue: ios_config - backup is not complete #42843) 

To minimize the output use the 'selective' Callback Plugin. 

* Functions:
  ----------
  * Backup switch's running-configuration only if config changes are detected
      For every host a subdirectory in the given base_dir will be created where
      all backup files (*.bck) will be stored including their backup timestamp 
        e.g. backup_dir/ROUTER01/ROUTER01_2018-08-25_22-40-16.bck

  * Save the modified running-config to startup-config on the switch (write memory)


Requirements
------------
napalm             - Installation: https://napalm.readthedocs.io/en/latest/

Ansible => 2.3     - network-cli (New in version 2.3.)


Role Variables
--------------

backup_dir: /tmp/backups
            Base directory where the backup files will be stored
              {{ backup_dir }}/{{ inventory_hostname }}/
              *.bck      ... Backup File

backup_files_group: group parameter of the 'file' module.
            If defined, the backup-file will be using the given
            group

Example Playbook
----------------

    ---
    - hosts: all

      roles:
      - role: jifox.cisco_backup


  Sample 'group_vars\all.yml
  -------------------------- 
    ---
    ansible_connection: network_cli
    ansible_network_os: ios
    ansible_become: yes
    ansible_become_method: enable
    ansible_user: cisco_ios
    ansible_ssh_pass: cisco_ios

    # directory where all the backups are stored
    backup_dir: /home/backups
    backup_files_group: backups

  Sample listing of backup_dir /home/backups/*/*
  ----------------------------------------------

    /home/backups/ROUTER01/ROUTER01_2018-08-25_22-40-16.bck



  Screen Output (with selective callback plugin): 
    $ ansible-playbook -i hosts.yml tasks/cisco_backup.yml
    ....
    # jifox.cisco_backup : Display Switch *************************************************************************************
      * ROUTER01                   - changed=False --------------------------------------------------
          (172.24.228.200) - LAB Environment:
          Catalyst L3 Switch Software (CAT9K_IOSXE), Version 16.6.4, RELEASE SOFTWARE (fc3)
    ...........
    # jifox.cisco_backup : Display Backup Action ******************************************************************************
      * ROUTER01                   - changed=False --------------------------------------------------
        Backup Configuration executed. Backup-File: /home/backups/ROUTER01/ROUTER01_2018-08-26_10-23-26.bck
    .

    # STATS *******************************************************************************************************************
    ROUTER01    : ok=18     changed=2       failed=0        unreachable=0


License
-------

license (GPLv3)

