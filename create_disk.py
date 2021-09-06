from azure.identity import ClientSecretCredential
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOptionTypes
import os

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


def create_disk(compute_client,group_name, location, disk_name):
    print('\nCreate (empty) managed Data Disk')
    async_disk_creation = compute_client.disks.begin_create_or_update(
        group_name,
        disk_name,
        {
            'location': location,
            'disk_size_gb': 1,
            'creation_data': {
            'create_option': DiskCreateOption.empty
            }
        })
    data_disk = async_disk_creation.result()
    print(data_disk)

def delete_disk(compute_client, group_name, disk_name):
    async_disk_delete = compute_client.disks.begin_delete(group_name, disk_name)
    print("disk delete : ", async_disk_delete.result())

def attach_disk(compute_client, group_name, vm_name, disk_name):
    vm = compute_client.virtual_machines.get(
    group_name,
    vm_name)
    print("vm details ", vm)

    managed_disk = compute_client.disks.get(group_name, disk_name)
    print("disk : ", managed_disk)

    vm.storage_profile.data_disks.append({
    'lun': 7, # You choose the value, depending of what is available for you
    'name': managed_disk.name,
    'create_option': DiskCreateOptionTypes.attach,
    'managed_disk': {
        'id': managed_disk.id
    }})
    async_update = compute_client.virtual_machines.begin_create_or_update(
    group_name,
    vm.name,
    vm,)
    print("Update status :  ",async_update.result())

def detach_disk(compute_client,  group_name, vm_name, disk_name):
    print('\nGet Virtual Machine by Name')
    virtual_machine = compute_client.virtual_machines.get(
        group_name,
        vm_name
    )
    print("machine :", virtual_machine)
    data_disks = virtual_machine.storage_profile.data_disks
    data_disks[:] = [disk for disk in data_disks if disk.name != disk_name]
    async_vm_update = compute_client.virtual_machines.begin_create_or_update(
        group_name,
        vm_name,
        virtual_machine
    )
    virtual_machine = async_vm_update.result()
    print(virtual_machine)


def update_os_disk_size(compute_client, group_name, vm_name):
    virtual_machine = compute_client.virtual_machines.get(
        group_name,
        vm_name
    )
    # Deallocating the VM (in preparation for a disk resize)
    print('\nDeallocating the VM (to prepare for a disk resize)')
    async_vm_deallocate = compute_client.virtual_machines.begin_deallocate(
        group_name, vm_name)
    print("Vm stop",async_vm_deallocate.result())

    print('\nUpdate OS disk size')
    os_disk_name = virtual_machine.storage_profile.os_disk.name
    os_disk = compute_client.disks.get(group_name, os_disk_name)
    if not os_disk.disk_size_gb:
        print("\tServer is not returning the OS disk size, possible bug in the server?")
        print("\tAssuming that the OS disk size is 30 GB")
        os_disk.disk_size_gb = 30

    os_disk.disk_size_gb += 10

    async_disk_update = compute_client.disks.begin_create_or_update(
        group_name,
        os_disk.name,
        os_disk
    )
    print(async_disk_update.result())

def create_or_update_vm_extention(compute_client, group_name, vm_name, ext_name, params_create):
     ext_poller = compute_client.virtual_machine_extensions.begin_create_or_update( group_name, vm_name,ext_name,params_create )
     print("vm extention: =", ext_poller.result())

if __name__ == "__main__":

    vm_name= "mymachine"
    group_name  = "disk-storage"
    disk_name = "mydisk"
    location = "eastus"
    credential, subscription_id = get_credentials()
    compute_client = ComputeManagementClient(credential, subscription_id)


    create_disk(compute_client, group_name, location, disk_name)
    attach_disk(compute_client, group_name, vm_name, disk_name)
    #delete_disk(compute_client, "disk", "ds")
    #detach_disk(compute_client, "vm",  "machine", "mydatadisk1")
    #update_os_disk_size(compute_client, "disk-storage", "mymachine")


    ext_type_name = 'CustomScriptForLinux'
    ext_name = 'etxscript-test'
    params_create = {
        'publisher': 'Microsoft.Azure.Extensions',
        'location' : "eastus",
        "type": "CustomScript",
        "typeHandlerVersion": "2.1",
        'protectedSettings':
        {
        'fileUris': ["https://raw.githubusercontent.com/MicrosoftDocs/mslearn-add-and-size-disks-in-azure-virtual-machines/master/add-data-disk.sh"],
        'commandToExecute' : "sh add-data-disk.sh"
        }
    }

    create_or_update_vm_extention(compute_client,group_name, vm_name, ext_name, params_create)
