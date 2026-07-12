terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

# Sufijo aleatorio para evitar colisiones de nombres globales (storage account, etc.)
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "test_rg" {
  name     = "rg-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "test_storage" {
  name                     = "st${var.project_name}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.test_rg.name
  location                 = azurerm_resource_group.test_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = var.tags
}

resource "azurerm_storage_container" "test_container" {
  name                  = "testdata"
  storage_account_name  = azurerm_storage_account.test_storage.name
  container_access_type = "private"
}

resource "azurerm_service_plan" "test_plan" {
  name                = "asp-${var.project_name}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.test_rg.name
  location            = azurerm_resource_group.test_rg.location
  os_type             = "Linux"
  sku_name            = "B1"
  tags                = var.tags
}

resource "azurerm_linux_web_app" "test_app" {
  name                = "app-${var.project_name}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.test_rg.name
  location            = azurerm_service_plan.test_plan.location
  service_plan_id     = azurerm_service_plan.test_plan.id
  tags                = var.tags

  site_config {
    always_on = false
    application_stack {
      python_version = "3.11"
    }
  }
}
