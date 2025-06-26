# Test the MCP tools

import pytest
from unittest.mock import patch, Mock, mock_open
import os
from server import assess_code_for_enterprise_standards, get_boilerplate_template

# Sample infrastructure code snippets for testing
SOME_BICEP_CODE = """
resource "azurerm_storage_account" "example" {
  name                     = "examplestorage"
  resource_group_name      = "example-rg"
  location                 = "westeurope"
  account_tier             = "Standard"
  account_replication_type = "GRS"
  
  network_rules {
    default_action = "Deny"
    ip_rules       = []
  }

  private_endpoint {
    name = "storage-pe"
    subnet_id = "/subscriptions/.../subnets/pe-subnet"
  }
}
"""

@pytest.mark.asyncio
async def test_assess_code_for_enterprise_standards():
  """
  Quick test to see if the function is working
  """
  result = await assess_code_for_enterprise_standards(SOME_BICEP_CODE)

  assert result is not None
  assert "compliant" in result.lower()

@pytest.mark.asyncio
async def test_get_boilerplate_template_with_templates():
    """
    Test the get_boilerplate_template function when templates exist (simplified version)
    """
    # Mock the templates directory and files
    mock_template_content = "// Test Bicep template content"
    
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('builtins.open', mock_open(read_data=mock_template_content)) as mock_file, \
         patch('server.AsyncAzureOpenAI') as mock_azure_client, \
         patch('server.AzureChatCompletion') as mock_chat_completion, \
         patch('server.Kernel') as mock_kernel, \
         patch('httpx.AsyncClient') as mock_http_client:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ['azure-webapp.bicep', 'azure-vm.bicep']
        
        # Mock HTTP client with async close method
        mock_http_instance = Mock()
        async def mock_aclose():
            pass
        mock_http_instance.aclose = mock_aclose
        mock_http_client.return_value = mock_http_instance
        
        # Mock LLM response
        mock_result = Mock()
        mock_result.content = "azure-webapp.bicep"
        
        mock_chat_instance = Mock()
        # Make the async method return a coroutine
        async def mock_get_chat(*args, **kwargs):
            return mock_result
        mock_chat_instance.get_chat_message_content = mock_get_chat
        mock_chat_completion.return_value = mock_chat_instance
        
        # Mock kernel
        mock_kernel_instance = Mock()
        mock_kernel.return_value = mock_kernel_instance
        
        # Call the function
        result = await get_boilerplate_template("I need a web application")
        
        # Assertions
        assert result is not None
        assert "azure-webapp.bicep" in result
        assert mock_template_content in result

@pytest.mark.asyncio
async def test_get_boilerplate_template_no_templates():
    """
    Test the get_boilerplate_template function when no templates exist
    """
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir:
        
        # Setup mocks for no templates
        mock_exists.return_value = True
        mock_listdir.return_value = []  # No .bicep files
        
        # Call the function
        result = await get_boilerplate_template("I need a template")
        
        # Assertions
        assert "No templates found" in result

@pytest.mark.asyncio 
async def test_get_boilerplate_template_missing_directory():
    """
    Test the get_boilerplate_template function when templates directory doesn't exist
    """
    with patch('os.path.exists') as mock_exists:
        
        # Setup mocks for missing directory
        mock_exists.return_value = False
        
        # Call the function
        result = await get_boilerplate_template("I need a template")
        
        # Assertions
        assert "No templates found" in result

@pytest.mark.asyncio
async def test_get_boilerplate_template_keyword_matching():
    """
    Test the get_boilerplate_template function using keyword matching fallback
    """
    mock_webapp_content = "// Azure Web App template content"
    mock_vm_content = "// Azure VM template content" 
    mock_aks_content = "// Azure AKS template content"
    
    def mock_open_function(filename, mode='r'):
        if 'azure-webapp.bicep' in filename:
            return mock_open(read_data=mock_webapp_content)()
        elif 'azure-vm.bicep' in filename:
            return mock_open(read_data=mock_vm_content)()
        elif 'azure-aks.bicep' in filename:
            return mock_open(read_data=mock_aks_content)()
        return mock_open(read_data="")()
    
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('builtins.open', side_effect=mock_open_function), \
         patch('os.getenv') as mock_getenv:
        
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ['azure-webapp.bicep', 'azure-vm.bicep', 'azure-aks.bicep']
        
        # Mock environment variables to trigger keyword matching fallback
        mock_getenv.side_effect = lambda key, default=None: {
            'AZURE_OPENAI_ENDPOINT': 'your_endpoint_here',  # This will trigger fallback
            'AZURE_OPENAI_API_KEY': 'your_api_key_here'
        }.get(key, default)
        
        # Test web app keyword matching
        result = await get_boilerplate_template("I need a web application")
        assert "azure-webapp.bicep" in result
        assert mock_webapp_content in result
        
        # Test VM keyword matching  
        result = await get_boilerplate_template("I need a virtual machine")
        assert "azure-vm.bicep" in result
        assert mock_vm_content in result
        
        # Test AKS keyword matching
        result = await get_boilerplate_template("I need a kubernetes cluster")
        assert "azure-aks.bicep" in result
        assert mock_aks_content in result