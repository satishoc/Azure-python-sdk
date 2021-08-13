import os
import traceback
from msrestazure.azure_exceptions import CloudError

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient


def get_credentials():
    """ 
    Get cred for authentication
    return: credentialObject and subscriptionId
    """
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ClientSecretCredential(
        client_id=os.environ['AZURE_CLIENT_ID'],
        client_secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant_id=os.environ['AZURE_TENANT_ID']
    )
    return credentials, subscription_id

def create_resource_group(resource_client, resource_group_name, location="", tags={}, **args):
    """ Create resource group """
    resource_group_params = {}
    if location:
        resource_group_params["location"]=location
    if tags:
        resource_group_params["tags"]=tags

    result = resource_client.resource_groups.create_or_update(
        resource_group_name, resource_group_params)
    print(f"Resource Group created : {result}")


def  create_virtual_network(network_clinet, resource_group_name,
        vnet_name, location, address_prefix, *kwargs):
    """ Craete virtual network """
    poller = network_client.virtual_networks.begin_create_or_update(
            resource_group_name,
            vnet_name,
            {
                "location": location,
                "address_space": {
                    "address_prefixes": [address_prefix]
                    }
                }
            )
    vnet_result = poller.result()
    print(f"Virtual network created: {vnet_result}")

def create_subnet(network_clinet, resource_group_name, vnet_name, subnet_name, address_prefix, **kwargs):
    poller = network_client.subnets.begin_create_or_update(
            resource_group_name,
            vnet_name,
            subnet_name,
            {
                "address_prefix": address_prefix
                }
            )
    subnet_result = poller.result()
    print(f"Subnet created :{subnet_result}")
    return subnet_result

def create_ip_address(network_client, resource_group_name, ip_name, location, **kwargs):
    poller = network_client.public_ip_addresses.begin_create_or_update(
            resource_group_name,
            ip_name,
            {
                "location": location,
                "sku": { "name": "Standard" },
                "public_ip_allocation_method": "Static",
                "public_ip_address_version" : "IPV4"
                }
            )
    ip_address_result = poller.result()
    print(f"Ip Address created : {ip_address_result}")
    return ip_address_result


def create_nic_or_network_interface_client(network_client, nic_name, location, resource_group_name, ip_config_name,
        subnet_result, ip_address_result):
    poller = network_client.network_interfaces.begin_create_or_update(
            resource_group_name,
            nic_name,
            {
                "location": location,
                "ip_configurations": [ {
                    "name": ip_config_name,
                    "subnet": { "id": subnet_result.id },
                    "public_ip_address": {"id": ip_address_result.id }
                    }]
                }
            )
    nic_result = poller.result()
    print(f"Nic created: {nic_result}")
    return nic_result

def create_virtual_machine(compute_client,resource_group_name, vm_name, location, user_name, password, nic_result):
    poller = compute_client.virtual_machines.begin_create_or_update(
            resource_group_name, 
            vm_name,
            {
                "location": location,
                "storage_profile": {
                    "image_reference": {
                        "publisher": 'Canonical',
                        "offer": "UbuntuServer",
                        "sku": "16.04.0-LTS",
                        "version": "latest"
                        }
                    },
                "hardware_profile": {
                    "vm_size": "Standard_DS1_v2"
                    },
                "os_profile": {
                    "computer_name": vm_name,
                    "admin_username": user_name,
                    "admin_password": password
                    },
                "network_profile": {
                    "network_interfaces": [{
                        "id": nic_result.id,
                        }]
                    }
                }
            )
    vm_result = poller.result()
    print(f"VM Created: {vm_result}")


def tag_vm(compute_client, resource_group_name, vm_name, location):
     vm_update = compute_client.virtual_machines.begin_create_or_update(
            resource_group_name,
            vm_name,
            {
                'location': location,
                'tags': {
                    'vm_cretaed_by': 'script',
                    'where': 'on azure'
                }
            }
        )
     result = vm_update.result()
     print(f"Vm_updat result : {result}")


def get_virtual_machine(compute_client, group_name, vm_name):
    virtual_machine = compute_client.virtual_machines.get(group_name, vm_name)
    print(f"virtual_machine: {virtual_machine}")
    return virtual_machine

def start_vm(compute_client, group_name, vm_name):
    vm_start = compute_client.virtual_machines.begin_start(group_name, vm_name)
    vm_start.result()

def stop_vm(compute_client, group_name, vm_name):
    vm_stop = compute_client.virtual_machines.begin_stop(group_name, vm_name)
    vm_stop.result()

def restart_vm(compute_client, group_name, vm_name):
    vm_restart = compute_client.virtual_machines.begin_restart(group_name, vm_name)
    vm_restart.result()




if __name__ == "__main__":

    resource_group_name = "groupname"
    location = "westus"
    vnet_name = "virtual_network_first"
    address_prefix = "10.0.0.0/16"
    address_prefix_subnet = "10.0.0.0/24"
    subnet_name = "firstsubnet"
    ip_name = "first_ip"
    ip_config_name = "ip_coinfiguration_name"
    nic_name = "First-nicname"
    vm_name= "script-machine"
    user_name="scriptmachine@oneconvergence12COM"
    password = "Oneconvergence@123PASS"


    credential, subscription_id = get_credentials()
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)
    try:
        create_resource_group(resource_client, resource_group_name, location)
        create_virtual_network(network_client, resource_group_name, vnet_name, location, address_prefix)
        subnet_result = create_subnet(network_client, resource_group_name, vnet_name, subnet_name, address_prefix_subnet)
        ip_address_result= create_ip_address(network_client, resource_group_name, ip_name, location)
        nic_result = create_nic_or_network_interface_client(network_client, nic_name, location, resource_group_name,
            ip_config_name, subnet_result, ip_address_result)
        create_virtual_machine(compute_client,resource_group_name, vm_name, location,user_name, password, nic_result)
        tag_vm(compute_client, resource_group_name, vm_name, location)
    except CloudError:
         print(f"VM operation failed {traceback.format_exc()}")
    else:
        print("All example operations completed successfully!")
    finally:
        print('\nDelete Resource Group')
        #When you delete a resource group, all of its resources are also deleted
        delete_resource_group = resource_client.resource_groups.begin_delete(resource_group_name)
        delete_resource_group.result()
