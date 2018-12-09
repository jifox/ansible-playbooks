#!/bin/bash

pa=`dirname "$0"`
cd ${pa}/..

# Disable terminal color sequences in captured output
export ANSIBLE_NOCOLOR=yes

# get script name
me=`basename "$0"`

############################################
# Start Compliance Report
#
starttime=`date '+%Y-%m-%d %H:%M:%S'`

# run compliance reports
/usr/bin/ansible-playbook -i inv_production.yml  ./run_compliance_report.yml > ./scripts/${me}.txt

endtime=`date '+%Y-%m-%d %H:%M:%S'`

echo "Runtime for Compliance Reports: $starttime to $endtime" >> ./scripts/${me}.txt


############################################
# Start Client Port Detail Report
#
starttime=`date '+%Y-%m-%d %H:%M:%S'`

/usr/bin/ansible-playbook -i inv_production.yml ./run_client_port_detail_report.yml >> ./scripts/${me}.txt

endtime=`date '+%Y-%m-%d %H:%M:%S'`

echo "Runtime for Client Port Detail Reports: $starttime to $endtime" >> ./scripts/${me}.txt

echo "  see:  http://ansible.lab.local:8080/reports/network_compliance_report.html" >> ./scripts/${me}.txt

# send email with ansible output in attachment
echo "Ansible Compliance Report Result. (  http://ansible.lab.local:8080/reports/network_compliance_report.html )" | mail -s "Cisco Reports" -r ansible@lab.com -a ./scripts/${me}.txt josef.fuchs@j-fuchs.at
