variable "location" {
  description = "Región de Azure donde se crean los recursos de prueba"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Prefijo usado para nombrar todos los recursos"
  type        = string
  default     = "jenkinsazuretest"
}

variable "environment" {
  description = "Entorno (dev, test, staging)"
  type        = string
  default     = "test"
}

variable "tags" {
  description = "Tags comunes aplicadas a todos los recursos"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Pipeline  = "Jenkins"
    Purpose   = "AzureTesting"
  }
}
