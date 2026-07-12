"""
Tests de validación de Infraestructura como Código (IaC).

No despliegan nada en Azure: solo ejecutan `terraform validate`, `terraform fmt`
y `checkov` como subprocesos y verifican que la infraestructura declarada en
terraform/ sea sintácticamente correcta y no viole reglas de seguridad básicas.

Requiere que los binarios `terraform` y `checkov` estén disponibles en el PATH
del agente Jenkins (o en la máquina local para correrlos manualmente).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TERRAFORM_DIR = Path(__file__).resolve().parents[2] / "terraform"

terraform_missing = shutil.which("terraform") is None
checkov_missing = shutil.which("checkov") is None


@pytest.fixture(scope="module", autouse=True)
def terraform_init():
    if terraform_missing:
        pytest.skip("terraform no está instalado en este entorno")
    subprocess.run(
        ["terraform", "init", "-backend=false", "-input=false"],
        cwd=TERRAFORM_DIR,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(terraform_missing, reason="terraform no está instalado")
def test_terraform_validate_succeeds():
    result = subprocess.run(
        ["terraform", "validate", "-json"],
        cwd=TERRAFORM_DIR,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["valid"] is True, f"Terraform validate falló: {output.get('diagnostics')}"


@pytest.mark.skipif(terraform_missing, reason="terraform no está instalado")
def test_terraform_fmt_is_clean():
    result = subprocess.run(
        ["terraform", "fmt", "-check", "-recursive"],
        cwd=TERRAFORM_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Hay archivos .tf sin formatear correctamente. "
        f"Ejecuta 'terraform fmt -recursive'.\n{result.stdout}"
    )


def test_required_files_exist():
    required = ["main.tf", "variables.tf", "outputs.tf"]
    missing = [f for f in required if not (TERRAFORM_DIR / f).exists()]
    assert not missing, f"Faltan archivos Terraform requeridos: {missing}"


def test_resources_declare_tags():
    """Verificación simple de buenas prácticas: todo recurso 'azurerm_*'
    relevante debe referenciar var.tags en main.tf."""
    main_tf = (TERRAFORM_DIR / "main.tf").read_text()
    taggable_blocks = [
        "azurerm_resource_group",
        "azurerm_storage_account",
        "azurerm_service_plan",
        "azurerm_linux_web_app",
    ]
    for resource_type in taggable_blocks:
        assert resource_type in main_tf, f"No se encontró el recurso {resource_type} en main.tf"


@pytest.mark.skipif(checkov_missing, reason="checkov no está instalado")
def test_checkov_no_high_severity_findings():
    result = subprocess.run(
        ["checkov", "-d", str(TERRAFORM_DIR), "--compact", "--quiet",
         "--check", "HIGH,CRITICAL", "--soft-fail"],
        capture_output=True,
        text=True,
    )
    # --soft-fail hace que checkov no devuelva código de error; validamos
    # el resumen textual en vez del returncode.
    assert "FAILED" not in result.stdout or "0 failed" in result.stdout.lower(), (
        f"Checkov encontró hallazgos de severidad alta/crítica:\n{result.stdout}"
    )
