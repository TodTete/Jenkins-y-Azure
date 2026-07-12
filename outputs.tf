output "resource_group_name" {
  description = "Nombre del resource group de prueba"
  value       = azurerm_resource_group.test_rg.name
}

output "storage_account_name" {
  description = "Nombre de la storage account de prueba"
  value       = azurerm_storage_account.test_storage.name
}

output "storage_container_name" {
  description = "Nombre del contenedor de blobs de prueba"
  value       = azurerm_storage_container.test_container.name
}

output "app_service_name" {
  description = "Nombre de la Web App desplegada"
  value       = azurerm_linux_web_app.test_app.name
}

output "app_service_default_hostname" {
  description = "URL por defecto de la Web App"
  value       = azurerm_linux_web_app.test_app.default_hostname
}
