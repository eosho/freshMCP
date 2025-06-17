// ------------------
//    PARAMETERS
// ------------------
@description('Name of your deployment environment.')
@allowed([
  'dev'
  'qa'
  'prod'
])
param environment string = 'dev'

@description('APIM SKU Tier to deploy. Choose between BasicV2 or StandardV2.')
@allowed([
  'BasicV2'
  'StandardV2'
])
param apimSku string = 'BasicV2'

@description('The name of the logger configured for Azure API Management (e.g., for App Insights).')
param apimLoggerName string = 'apim-logger'

@description('The Azure region where resources will be deployed.')
param location string = resourceGroup().location

@description('URL path prefix for the Cosmos MCP API within API Management.')
param cosmosAPIPath string = 'cosmos'

@description('URL path prefix for the Azure AI Search MCP API within API Management.')
param searchAPIPath string = 'search'

@description('Resource tags')
param tags object = {
  'azd-env-name': environment
}
// ------------------
//    VARIABLES
// ------------------

var resourceSuffix = uniqueString(subscription().id, resourceGroup().id)
var apiManagementName = 'apim-${resourceSuffix}'
var acrPullRole = resourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
// var apimContributorRoleDefinitionID = resourceId('Microsoft.Authorization/roleDefinitions', '312a565d-c81f-4fd8-895a-4e21e48d571c')

// ------------------
//    RESOURCES
// ------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'workspace-${resourceSuffix}'
  location: location
  tags: tags
  properties: any({
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
  })
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: 'acr${resourceSuffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  tags: union(tags, {
    'azd-container-registry': 'true'
  })
  properties: {
    adminUserEnabled: true
    anonymousPullEnabled: false
    dataEndpointEnabled: false
    encryption: {
      status: 'disabled'
    }
    metadataSearch: 'Disabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
      exportPolicy: {
        status: 'enabled'
      }
      azureADAuthenticationAsArmPolicy: {
        status: 'enabled'
      }
      softDeletePolicy: {
        retentionDays: 7
        status: 'disabled'
      }
    }
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: 'aca-env-${resourceSuffix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerAppUAI 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' = {
  name: 'aca-mi-${resourceSuffix}'
  location: location
  tags: tags
}

resource containerAppUAIRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, containerAppUAI.id, acrPullRole)
  properties: {
    roleDefinitionId: acrPullRole
    principalId: containerAppUAI.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosMCPServerContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'aca-cosmos-${resourceSuffix}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${containerAppUAI.id}': {}
    }
  }
  tags: union(tags, {
    'azd-service-name': 'cosmos-mcp'
  })
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8001
        allowInsecure: false
      }
      registries: [
        {
          identity: containerAppUAI.id
          server: containerRegistry.properties.loginServer
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'aca-${resourceSuffix}'
          image: 'docker.io/jfxs/hello-world:latest'
          resources: {
            cpu: json('.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource searchMCPServerContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'aca-search-${resourceSuffix}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${containerAppUAI.id}': {}
    }
  }
  tags: union(tags, {
    'azd-service-name': 'search-mcp'
  })
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8002
        allowInsecure: false
      }
      registries: [
        {
          identity: containerAppUAI.id
          server: containerRegistry.properties.loginServer
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'aca-${resourceSuffix}'
          image: 'docker.io/jfxs/hello-world:latest'
          resources: {
            cpu: json('.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'insights-${resourceSuffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ------------------
//    RESOURCES
// ------------------

resource apimService 'Microsoft.ApiManagement/service@2024-06-01-preview' = {
  name: apiManagementName
  location: location
  tags: tags
  sku: {
    name: apimSku
    capacity: 1
  }
  properties: {
    publisherEmail: 'noreply@microsoft.com'
    publisherName: 'Microsoft'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Create a logger only if we have an App Insights ID and instrumentation key.
resource apimLogger 'Microsoft.ApiManagement/service/loggers@2021-12-01-preview' = {
  name: apimLoggerName
  parent: apimService
  properties: {
    credentials: {
      instrumentationKey: applicationInsights.properties.InstrumentationKey
    }
    description: 'APIM Logger'
    isBuffered: false
    loggerType: 'applicationInsights'
    resourceId: applicationInsights.id
  }
}

module cosmosAPIModule '../src/cosmos/apim-api/api.bicep' = {
  name: 'cosmosAPIModule'
  params: {
    apimServiceName: apimService.name
    APIPath: cosmosAPIPath
    APIServiceURL: 'https://${cosmosMCPServerContainerApp.properties.configuration.ingress.fqdn}/${cosmosAPIPath}'
  }
}

module searchAPIModule '../src/search/apim-api/api.bicep' = {
  name: 'searchAPIModule'
  params: {
    apimServiceName: apimService.name
    APIPath: searchAPIPath
    APIServiceURL: 'https://${searchMCPServerContainerApp.properties.configuration.ingress.fqdn}/${searchAPIPath}'
  }
}

// Ignore the subscription that gets created in the APIM module and create three new ones for this lab.
resource apimSubscription 'Microsoft.ApiManagement/service/subscriptions@2024-06-01-preview' = {
  name: 'apim-subscription'
  parent: apimService
  properties: {
    allowTracing: true
    displayName: 'Generic APIM Subscription'
    scope: '/apis'
    state: 'active'
  }
}

// resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' =  {
//     scope: apimService
//     name: guid(subscription().id, resourceGroup().id, apimContributorRoleDefinitionID)
//     properties: {
//         roleDefinitionId: apimContributorRoleDefinitionID
//         principalId: containerAppUAI.properties.principalId
//         principalType: 'ServicePrincipal'
//     }
// }

// ------------------
//    OUTPUTS
// ------------------
output containerRegistryName string = containerRegistry.name

output cosmosMCPServerContainerAppResourceName string = cosmosMCPServerContainerApp.name
output cosmosMCPServerContainerAppFQDN string = cosmosMCPServerContainerApp.properties.configuration.ingress.fqdn

output searchMCPServerContainerAppResourceName string = searchMCPServerContainerApp.name
output searchMCPServerContainerAppFQDN string = searchMCPServerContainerApp.properties.configuration.ingress.fqdn

output applicationInsightsAppId string = applicationInsights.id
output applicationInsightsName string = applicationInsights.name

output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId

output apimServiceId string = apimService.id
output apimResourceName string = apimService.name
output apimResourceGatewayURL string = apimService.properties.gatewayUrl

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
