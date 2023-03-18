# VMware VM Deployment playbook



## General

This is a proof of concept i created to test and prove the capabilities of Ansible for incoorperating it in a already established datacenter with multi-tenancy.

This playbook was designed to be used in conjuction with AWX ('free' version of Tower). You will have to create a secret and supply the Job template with it or run it from commandline with --vault-secret.

This playbook is able to create VMs with static IP and join them to configured domain in vars/cust/<name>.yml

## Ansible Vault

vars/global_vars.yml contains vault variables. Use the correct vault secret i AWX, for each vCenter.

## requirements

it uses default modules, no need to install any dependancies.