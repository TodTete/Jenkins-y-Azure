"""
Smoke tests post-despliegue: confirman que Terraform realmente creó los
recursos esperados en Azure (resource group, storage account, web app) y que
tienen el estado/configuración esperada.

Se ejecutan solo cuando DEPLOY_TO_AZURE=true en el Jenkinsfile, después del
`terraform apply`. Usan el Azure SDK (azure-mgmt-*) con las credenciales del
Service Principal.
"""

import pytest


@pytest.fixture(scope="module")
def resource_client(azure_credential, subscription_id):
    pytest.importorskip("azure.mgmt.resource")
    from azure.mgmt.resource import ResourceManagementClient

    return ResourceManagementClient(azure_credential, subscription_id)


@pytest.fixture(scope="module")
def storage_client(azure_credential, subscription_id):
    pytest.importorskip("azure.mgmt.storage")
    from azure.mgmt.storage import StorageManagementClient

    return StorageManagementClient(azure_credential, subscription_id)


@pytest.fixture(scope="module")
def web_client(azure_credential, subscription_id):
    pytest.importorskip("azure.mgmt.web")
    from azure.mgmt.web import WebSiteManagementClient

    return WebSiteManagementClient(azure_credential, subscription_id)


class TestResourceGroup:
    def test_resource_group_exists(self, resource_client, resource_group_name):
        rg = resource_client.resource_groups.get(resource_group_name)
        assert rg.name == resource_group_name

    def test_resource_group_is_succeeded(self, resource_client, resource_group_name):
        rg = resource_client.resource_groups.get(resource_group_name)
        assert rg.properties.provisioning_state == "Succeeded"

    def test_resource_group_has_expected_tags(self, resource_client, resource_group_name):
        rg = resource_client.resource_groups.get(resource_group_name)
        assert rg.tags is not None
        assert rg.tags.get("ManagedBy") == "Terraform"
        assert rg.tags.get("Pipeline") == "Jenkins"


class TestStorageAccount:
    def test_storage_account_exists(self, storage_client, resource_group_name, storage_account_name):
        account = storage_client.storage_accounts.get_properties(
            resource_group_name, storage_account_name
        )
        assert account.name == storage_account_name

    def test_storage_account_uses_tls_1_2(self, storage_client, resource_group_name, storage_account_name):
        account = storage_client.storage_accounts.get_properties(
            resource_group_name, storage_account_name
        )
        assert account.minimum_tls_version == "TLS1_2"

    def test_storage_container_exists(self, storage_client, resource_group_name, storage_account_name):
        containers = list(
            storage_client.blob_containers.list(resource_group_name, storage_account_name)
        )
        names = [c.name for c in containers]
        assert "testdata" in names


class TestWebApp:
    def test_web_app_exists_and_running(self, web_client, resource_group_name, app_service_name):
        app = web_client.web_apps.get(resource_group_name, app_service_name)
        assert app.name == app_service_name
        assert app.state == "Running"

    def test_web_app_uses_linux(self, web_client, resource_group_name, app_service_name):
        app = web_client.web_apps.get(resource_group_name, app_service_name)
        assert "linux" in (app.kind or "").lower()
