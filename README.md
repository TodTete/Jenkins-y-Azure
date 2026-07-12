# jenkins-azure-testing

Pipeline de Jenkins con suite de pruebas para infraestructura y aplicaciones en **Microsoft Azure**. Incluye validación de IaC (Terraform + Checkov), tests unitarios, despliegue de recursos de prueba y tests de integración/conectividad con el Azure SDK.

## Estructura

```
.
├── Jenkinsfile                 # Pipeline declarativo (stages descritos abajo)
├── terraform/                  # IaC: resource group, storage account, web app
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── src/
│   └── azure_helpers.py        # Funciones puras reutilizadas por pipeline y tests
├── tests/
│   ├── unit/                   # Sin red, sin Azure — feedback rápido
│   │   └── test_azure_helpers.py
│   ├── iac/                    # Validan terraform validate/fmt + checkov
│   │   └── test_terraform_validate.py
│   └── integration/            # Requieren recursos desplegados en Azure
│       ├── test_deployment_smoke.py
│       └── test_connectivity.py
├── scripts/
│   ├── azure_login.sh
│   ├── deploy.sh
│   └── destroy.sh
├── conftest.py                 # Fixtures compartidas (credenciales, nombres de recursos)
├── requirements.txt
├── pytest.ini
└── .gitignore
```

## Qué prueba cada capa

| Capa | Qué valida | Requiere Azure real |
|---|---|---|
| `tests/unit` | Lógica de nombres de recursos, tags, parseo de outputs | No |
| `tests/iac` | `terraform validate`, `terraform fmt`, escaneo de seguridad con Checkov | No (solo binarios locales) |
| `tests/integration` | Que los recursos existan, tengan el estado/config esperado, y respondan (auth, lectura/escritura de blobs, healthcheck HTTP) | Sí |

## Etapas del Jenkinsfile

1. Checkout
2. Setup Python (venv + requirements)
3. Lint (`flake8`)
4. Unit Tests (`pytest tests/unit`)
5. Azure Login (Service Principal)
6. Terraform Init & Validate
7. IaC Security Scan (Checkov)
8. IaC Test Suite (`pytest tests/iac`)
9. Terraform Plan
10. Deploy to Azure *(solo si `DEPLOY_TO_AZURE=true`)*
11. Integration & Smoke Tests *(solo si `DEPLOY_TO_AZURE=true`)*
12. Post: `terraform destroy` automático si `DESTROY_AFTER_TESTS=true`, logout de `az`, y archivado de reportes JUnit

## Configuración inicial

### 1. Crear un Service Principal en Azure

```bash
az ad sp create-for-rbac --name "jenkins-azure-testing" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>
```

Esto devuelve `appId` (client id), `password` (client secret) y `tenant`.

### 2. Configurar credenciales en Jenkins

En **Manage Jenkins → Credentials**, crea 4 credenciales tipo *Secret text*:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

### 3. Herramientas requeridas en el agente Jenkins

- Python 3.11+
- Terraform >= 1.5
- Azure CLI (`az`)
- Acceso a red saliente hacia `management.azure.com` y `*.blob.core.windows.net`

## Uso local (sin Jenkins)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Tests que no requieren Azure
pytest tests/unit tests/iac -v

# Desplegar infraestructura de prueba
export AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... AZURE_TENANT_ID=... AZURE_SUBSCRIPTION_ID=...
./scripts/azure_login.sh
./scripts/deploy.sh   # imprime RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME, APP_SERVICE_NAME

export RESOURCE_GROUP_NAME=... STORAGE_ACCOUNT_NAME=... APP_SERVICE_NAME=...
pytest tests/integration -v

# Limpiar recursos
./scripts/destroy.sh
```

## Publicar en GitHub

```bash
cd jenkins-azure-testing
git init
git add .
git commit -m "Initial commit: pipeline Jenkins + tests para Azure"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/jenkins-azure-testing.git
git push -u origin main
```

Luego, en Jenkins, crea un **Pipeline job** apuntando a este repositorio y con "Script Path" = `Jenkinsfile` (o usa *Multibranch Pipeline* para detectarlo automáticamente).

## Notas de seguridad

- Nunca commitees archivos `.tfvars`, `.tfstate` ni credenciales — ya están en `.gitignore`.
- El Service Principal debería tener el mínimo privilegio necesario (idealmente scopeado a un resource group dedicado a pruebas, no a toda la suscripción).
- `DEPLOY_TO_AZURE` está en `false` por defecto para evitar crear recursos reales accidentalmente al correr el pipeline.
