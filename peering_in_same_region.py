import os
import traceback
from msrestazure.azure_exceptions import CloudError

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient


from azure.mgmt.network.v2020_06_01.models import SecurityRule

from azure.mgmt.network.v2020_06_01.models import NetworkSecurityGroup

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


def create_subnet(network_clinet, resource_group_name, vnet_name, subnet_name, address_prefix,nsg_result, **kwargs):
    poller = network_client.subnets.begin_create_or_update(
            resource_group_name,
            vnet_name,
            subnet_name,
            {
                "address_prefix": address_prefix,
                "network_security_group":{
                    "id": nsg_result.id,
                    }  
                }
            )
    subnet_result = poller.result()
    print(f"Subnet created :{subnet_result}")
    return subnet_result


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


def create_network_security_rule(network_client, resource_group_name, nsg_name, security_rule_name, security_rule_params):
    poller = network_client.security_rules.begin_create_or_update(resource_group_name,nsg_name,security_rule_name=security_rule_name,
            security_rule_parameters=security_rule_params)
    sec_rule_result = poller.result()
    return sec_rule_result

def create_peer(network_client, resource_group_name, virtual_network_name, vnet_peer_name, remote_vnet):
    vn = network_client.virtual_networks.get(resource_group_name, remote_vnet)
     
    async_creation = network_client.virtual_network_peerings.begin_create_or_update(
        resource_group_name,
        virtual_network_name,
        vnet_peer_name,
        {
             "allowVirtualNetworkAccess": True,
             "allowForwardedTraffic": True,
             "allowGatewayTransit": False,
             "useRemoteGateways": False,
            'remote_virtual_network': {
               'id': vn.id
            }
        }
    )
    print("PEER RESULT:",async_creation.result())




if __name__ == "__main__":


    vnet_peer_name0 = "peer1"
    vnet_peer_name1 = "peer2"
    

    resource_group_name = "groupidname"
    location = "westus"
    vnet_name0 = "virtual_network_first0"
    address_prefix0 = "10.0.0.0/16"
    address_prefix1 = "10.1.0.0/16"
    vnet_name1 = "virtual_network_first1"
    address_prefix_subnet0 = "10.0.0.0/24"
    subnet_name0 = "firstsubnet0"
    subnet_name1 = "firstsubnet1"
    address_prefix_subnet1 = "10.1.0.0/24"
    ip_name0 = "first_ip"
    ip_name1 ="second_ip"
    ip_config_name0 = "ip_coinfiguration_name0"
    nic_name0 = "First-nicname0"
    nic_name1 = "First-nicname1"
    ip_config_name1 = "ip_coinfiguration_name1"
    user_name0="scriptmachineoneconvergence12COM"
    vm_name0= "script-machine0"
    vm_name1= "script-machine1"
    password0 = "Oneconvergence123PASS"
    user_name1="scriptmachineoneconvergence12COMQ"
    password1 = "Oneconvergence123PASS1"
    sec_rule_name = "testrule"
    nsg_name = "testnsg"
    """sec_rule_params = SecurityRule(
            id="testrule",
            name=sec_rule_name,
            protocol="Tcp",
            source_port_range="*",
            destination_port_range="22",
            source_address_prefix="*",
            destination_address_prefix="*",
            access="Allow",
            direction="inbound",
            priority=100,
            )"""








    credential, subscription_id = get_credentials()
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)
    create_resource_group(resource_client, resource_group_name, location)



    nsg_params = NetworkSecurityGroup()
    nsg_params.location = location
    nsg_params.security_rules = [SecurityRule(
            id="testrule",
            name=sec_rule_name,
            protocol="*",
            source_port_range="*",
            destination_port_range="22",
            source_address_prefix="*",
            destination_address_prefix="*",
            access="Allow",
            direction="inbound",
            priority=4000,
            )]
    poller = network_client.network_security_groups.begin_create_or_update(resource_group_name, "testnsg", parameters=nsg_params)
    nsg_result = poller.result()

    poller1 = network_client.network_security_groups.begin_create_or_update(resource_group_name, "testnsg1", parameters=nsg_params)
    nsg_result1 = poller.result()


    create_virtual_network(network_client, resource_group_name, vnet_name0, location, address_prefix0)
    #network_security_group = create_network_security_rule(network_client, resource_group_name,"testnsg", sec_rule_name,sec_rule_params)
    subnet_result = create_subnet(network_client, resource_group_name, vnet_name0, subnet_name0 , address_prefix_subnet0, nsg_result)
    ip_address_result= create_ip_address(network_client, resource_group_name, ip_name0, location)
    nic_result = create_nic_or_network_interface_client(network_client, nic_name0, location, resource_group_name,
        ip_config_name0, subnet_result, ip_address_result)
    create_virtual_machine(compute_client,resource_group_name, vm_name0, location,"satish", "satish@KUMAR", nic_result)
    
    
    create_virtual_network(network_client, resource_group_name, vnet_name1, location, address_prefix1)
    subnet_result1 = create_subnet(network_client, resource_group_name, vnet_name1, subnet_name1 , address_prefix_subnet1, nsg_result1)
    ip_address_result1= create_ip_address(network_client, resource_group_name, ip_name1, location)
    nic_result1 = create_nic_or_network_interface_client(network_client, nic_name1, location, resource_group_name,
        ip_config_name1, subnet_result1, ip_address_result1)
    create_virtual_machine(compute_client,resource_group_name, vm_name1, location,"satish", "satish@KUMAR", nic_result1)

    create_peer(network_client, resource_group_name, vnet_name0, vnet_peer_name0,vnet_name1)
    create_peer(network_client, resource_group_name, vnet_name1, vnet_peer_name1, vnet_name0)
