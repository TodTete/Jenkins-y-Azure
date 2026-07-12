"""
Funciones auxiliares puras (sin llamadas de red) reutilizadas por el
pipeline y por los tests. Mantenerlas sin dependencias de Azure facilita
probarlas como unit tests rápidos y deterministas.
"""

from __future__ import annotations

import re

MAX_STORAGE_ACCOUNT_NAME_LEN = 24
STORAGE_ACCOUNT_NAME_RE = re.compile(r"^[a-z0-9]{3,24}$")


def build_resource_name(project: str, environment: str, resource_type: str, suffix: str) -> str:
    """Construye un nombre de recurso siguiendo la convención:
    <tipo>-<proyecto>-<entorno>-<sufijo>

    Ej: build_resource_name("myapp", "test", "rg", "ab12cd")
        -> "rg-myapp-test-ab12cd"
    """
    if not all([project, environment, resource_type, suffix]):
        raise ValueError("Todos los componentes del nombre son obligatorios")
    return f"{resource_type}-{project}-{environment}-{suffix}".lower()


def build_storage_account_name(project: str, suffix: str) -> str:
    """Las storage accounts de Azure solo permiten minúsculas/números y
    máximo 24 caracteres, sin guiones."""
    name = f"st{project}{suffix}".lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name[:MAX_STORAGE_ACCOUNT_NAME_LEN]


def is_valid_storage_account_name(name: str) -> bool:
    return bool(STORAGE_ACCOUNT_NAME_RE.match(name))


def merge_tags(base_tags: dict, extra_tags: dict | None = None) -> dict:
    """Combina tags por defecto con tags adicionales, sin mutar los originales."""
    merged = dict(base_tags)
    if extra_tags:
        merged.update(extra_tags)
    return merged


def parse_terraform_output(raw_output: str, key: str) -> str:
    """Extrae un valor simple de la salida JSON de `terraform output -json`.
    Se usa una implementación mínima basada en el módulo json estándar,
    delegando el parseo real al llamador si el dict ya viene decodificado.
    """
    import json

    data = json.loads(raw_output)
    if key not in data:
        raise KeyError(f"'{key}' no encontrado en la salida de Terraform")
    return data[key]["value"]
