// Azure Virtual Machine with managed disks and network security
// This template creates a secure Linux virtual machine

@description('The name of the Virtual Machine')
param vmName string = 'vm-${uniqueString(resourceGroup().id)}'

@description('The location for all resources')
param location string = resourceGroup().location

@description('Admin username for the Virtual Machine')
param adminUsername string

@description('SSH public key for authentication')
@secure()
param sshPublicKey string

@description('Size of the Virtual Machine')
@allowed([
  'Standard_B1s'
  'Standard_B2s'
  'Standard_D2s_v3'
  'Standard_D4s_v3'
  'Standard_D8s_v3'
])
param vmSize string = 'Standard_B2s'

@description('Operating System for the Virtual Machine')
@allowed([
  'Ubuntu-2004'
  'Ubuntu-2204'
  'RHEL-8'
  'RHEL-9'
])
param osType string = 'Ubuntu-2204'

@description('Disk size for OS disk in GB')
param osDiskSizeGB int = 128

var networkSecurityGroupName = 'nsg-${vmName}'
var virtualNetworkName = 'vnet-${vmName}'
var subnetName = 'subnet-${vmName}'
var publicIPAddressName = 'pip-${vmName}'
var networkInterfaceName = 'nic-${vmName}'
var subnetRef = resourceId('Microsoft.Network/virtualNetworks/subnets', virtualNetworkName, subnetName)

// OS Image configuration
var osImageConfig = {
  'Ubuntu-2004': {
    publisher: 'Canonical'
    offer: '0001-com-ubuntu-server-focal'
    sku: '20_04-lts-gen2'
    version: 'latest'
  }
  'Ubuntu-2204': {
    publisher: 'Canonical'
    offer: '0001-com-ubuntu-server-jammy'
    sku: '22_04-lts-gen2'
    version: 'latest'
  }
  'RHEL-8': {
    publisher: 'RedHat'
    offer: 'RHEL'
    sku: '8-LVM'
    version: 'latest'
  }
  'RHEL-9': {
    publisher: 'RedHat'
    offer: 'RHEL'
    sku: '9-LVM'
    version: 'latest'
  }
}

// Network Security Group
resource networkSecurityGroup 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: networkSecurityGroupName
  location: location
  properties: {
    securityRules: [
      {
        name: 'SSH'
        properties: {
          description: 'Allow SSH'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 1001
          direction: 'Inbound'
        }
      }
      {
        name: 'HTTPS'
        properties: {
          description: 'Allow HTTPS'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 1002
          direction: 'Inbound'
        }
      }
    ]
  }
}

// Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: virtualNetworkName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix: '10.0.0.0/24'
          networkSecurityGroup: {
            id: networkSecurityGroup.id
          }
        }
      }
    ]
  }
}

// Public IP Address
resource publicIPAddress 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: publicIPAddressName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: {
      domainNameLabel: toLower('${vmName}-${uniqueString(resourceGroup().id)}')
    }
  }
}

// Network Interface
resource networkInterface 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: networkInterfaceName
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIPAddress.id
          }
          subnet: {
            id: subnetRef
          }
        }
      }
    ]
  }
  dependsOn: [
    virtualNetwork
  ]
}

// Virtual Machine
resource virtualMachine 'Microsoft.Compute/virtualMachines@2023-09-01' = {
  name: vmName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: osImageConfig[osType]
      osDisk: {
        name: '${vmName}-osdisk'
        caching: 'ReadWrite'
        createOption: 'FromImage'
        diskSizeGB: osDiskSizeGB
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: networkInterface.id
        }
      ]
    }
    diagnosticsProfile: {
      bootDiagnostics: {
        enabled: false
      }
    }
  }
}

// VM Extension for Azure Monitor Agent
resource azureMonitorAgent 'Microsoft.Compute/virtualMachines/extensions@2023-09-01' = {
  parent: virtualMachine
  name: 'AzureMonitorLinuxAgent'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Monitor'
    type: 'AzureMonitorLinuxAgent'
    typeHandlerVersion: '1.0'
    autoUpgradeMinorVersion: true
    enableAutomaticUpgrade: true
  }
}

// Diagnostic settings for monitoring
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${vmName}-diagnostics'
  scope: virtualMachine
  properties: {
    workspaceId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/shared-resources/providers/Microsoft.OperationalInsights/workspaces/constoso-logs'
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
  }
}

// Outputs
output vmName string = virtualMachine.name
output publicIPAddress string = publicIPAddress.properties.ipAddress
output fqdn string = publicIPAddress.properties.dnsSettings.fqdn
output sshCommand string = 'ssh ${adminUsername}@${publicIPAddress.properties.dnsSettings.fqdn}'
output principalId string = virtualMachine.identity.principalId