// Azure Kubernetes Service (AKS) cluster with best practices
// This template creates a production-ready AKS cluster with security features

@description('The name of the AKS cluster')
param aksClusterName string = 'aks-${uniqueString(resourceGroup().id)}'

@description('The location for all resources')
param location string = resourceGroup().location

@description('The Kubernetes version for the AKS cluster')
param kubernetesVersion string = '1.28.3'

@description('The number of nodes in the default node pool')
param nodeCount int = 3

@description('The size of the nodes in the default node pool')
@allowed([
  'Standard_D2s_v3'
  'Standard_D4s_v3'
  'Standard_D8s_v3'
  'Standard_D16s_v3'
])
param nodeVmSize string = 'Standard_D2s_v3'

@description('Enable system-assigned managed identity')
param enableManagedIdentity bool = true

@description('Enable Azure RBAC for Kubernetes authorization')
param enableAzureRBAC bool = true

@description('Enable network policy (Azure or Calico)')
@allowed([
  'azure'
  'calico'
  'none'
])
param networkPolicy string = 'azure'

@description('Enable HTTP application routing')
param enableHttpApplicationRouting bool = false

@description('Enable Azure Monitor for containers')
param enableMonitoring bool = true

var logAnalyticsWorkspaceName = 'law-${aksClusterName}'
var aksClusterIdentityName = 'id-${aksClusterName}'
var vnetName = 'vnet-${aksClusterName}'
var aksSubnetName = 'subnet-aks'
var nodeResourceGroupName = 'rg-${aksClusterName}-nodes'

// Log Analytics Workspace for AKS monitoring
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (enableMonitoring) {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// User-assigned managed identity for AKS
resource aksClusterIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = if (enableManagedIdentity) {
  name: aksClusterIdentityName
  location: location
}

// Virtual Network for AKS
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: aksSubnetName
        properties: {
          addressPrefix: '10.0.1.0/24'
          serviceEndpoints: [
            {
              service: 'Microsoft.ContainerRegistry'
            }
            {
              service: 'Microsoft.Storage'
            }
          ]
        }
      }
    ]
  }
}

// AKS Cluster
resource aksCluster 'Microsoft.ContainerService/managedClusters@2023-10-01' = {
  name: aksClusterName
  location: location
  identity: enableManagedIdentity ? {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${aksClusterIdentity.id}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    nodeResourceGroup: nodeResourceGroupName
    dnsPrefix: aksClusterName
    agentPoolProfiles: [
      {
        name: 'systempool'
        count: nodeCount
        vmSize: nodeVmSize
        osType: 'Linux'
        mode: 'System'
        type: 'VirtualMachineScaleSets'
        availabilityZones: [
          '1'
          '2'
          '3'
        ]
        enableAutoScaling: true
        minCount: 1
        maxCount: 10
        maxPods: 30
        vnetSubnetID: '${virtualNetwork.id}/subnets/${aksSubnetName}'
        osDiskSizeGB: 128
        osDiskType: 'Managed'
        kubeletDiskType: 'OS'
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: networkPolicy != 'none' ? networkPolicy : null
      serviceCidr: '10.1.0.0/16'
      dnsServiceIP: '10.1.0.10'
    }
    aadProfile: enableAzureRBAC ? {
      managed: true
      enableAzureRBAC: true
    } : null
    addonProfiles: {
      httpApplicationRouting: {
        enabled: enableHttpApplicationRouting
      }
      omsagent: enableMonitoring ? {
        enabled: true
        config: {
          logAnalyticsWorkspaceResourceID: logAnalyticsWorkspace.id
        }
      } : {
        enabled: false
      }
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'true'
          rotationPollInterval: '2m'
        }
      }
    }
    apiServerAccessProfile: {
      enablePrivateCluster: false
      authorizedIPRanges: []
    }
    autoScalerProfile: {
      'scale-down-delay-after-add': '10m'
      'scale-down-unneeded-time': '10m'
      'scale-down-utilization-threshold': '0.5'
      'max-graceful-termination-sec': '600'
      'new-pod-scale-up-delay': '0s'
    }
    securityProfile: {
      workloadIdentity: {
        enabled: true
      }
      imageCleaner: {
        enabled: true
        intervalHours: 24
      }
    }
  }
}

// Role assignment for AKS to access virtual network
resource networkContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableManagedIdentity) {
  name: guid(aksClusterIdentity.id, virtualNetwork.id, 'Network Contributor')
  scope: virtualNetwork
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4d97b98b-1d4f-4787-a291-c67834d212e7') // Network Contributor
    principalId: aksClusterIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Diagnostic settings for AKS cluster
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${aksClusterName}-diagnostics'
  scope: aksCluster
  properties: {
    workspaceId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/shared-resources/providers/Microsoft.OperationalInsights/workspaces/constoso-logs'
    logs: [
      {
        category: 'kube-apiserver'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'kube-audit'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'kube-controller-manager'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'kube-scheduler'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'cluster-autoscaler'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
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
output aksClusterName string = aksCluster.name
output aksClusterFQDN string = aksCluster.properties.fqdn
output aksClusterResourceId string = aksCluster.id
output kubernetesVersion string = aksCluster.properties.kubernetesVersion
output nodeResourceGroup string = aksCluster.properties.nodeResourceGroup
output managedIdentityPrincipalId string = enableManagedIdentity ? aksClusterIdentity.properties.principalId : aksCluster.identity.principalId
output kubectlCommand string = 'az aks get-credentials --resource-group ${resourceGroup().name} --name ${aksCluster.name}'