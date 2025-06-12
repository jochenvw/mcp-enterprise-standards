# Test the assess_code_for_enterprise_standards function

import pytest
from unittest.mock import patch, Mock
from server import assess_code_for_enterprise_standards

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