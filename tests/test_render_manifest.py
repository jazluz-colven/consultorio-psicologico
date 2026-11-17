"""Contrato del manifiesto de Render para la Spec 019 (T14).

El archivo ``render.yaml`` es un Blueprint de Render. Este test lo lee como
texto y valida solo la estructura mínima que fija el plan D11, sin añadir
dependencias: no se usa PyYAML (Spec 019, RNF-8 / D1).

Referencias: ``specs/019_migrar-postgresql/spec.md`` (RF-1, RF-2, RF-3, RF-15;
RNF-1, RNF-3, RNF-6, RNF-7), ``plan.md`` D11 y ``tasks.md`` T14.
"""

from __future__ import annotations

import re
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "render.yaml"

_FIELD_RE = re.compile(
    r"^(?P<indent>\s*)(?:-\s+)?(?P<key>[A-Za-z_][\w-]*):(?:\s*(?P<value>.*))?$"
)


def _clean_lines() -> list[str]:
    """Return non-empty lines with YAML comments and indentation intact."""
    lines: list[str] = []
    for raw in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        without_comment = raw.split("#", 1)[0].rstrip()
        if without_comment.strip():
            lines.append(without_comment)
    return lines


def _service_fields() -> dict[str, str]:
    """Return scalar fields of the single web service in the Blueprint."""
    fields: dict[str, str] = {}
    in_services = False
    for line in _clean_lines():
        match = _FIELD_RE.match(line)
        if not match:
            continue
        indent = len(match.group("indent"))
        key = match.group("key")
        value = (match.group("value") or "").strip().strip("'\"")
        if key == "services" and indent == 0:
            in_services = True
            continue
        if not in_services:
            continue
        if indent == 2 and key == "type":
            fields["type"] = value
        elif indent == 4:
            fields[key] = value
    return fields


def _env_vars() -> dict[str, dict[str, str]]:
    """Return ``{key: {attribute: value}}`` for the service's ``envVars``."""
    entries: dict[str, dict[str, str]] = {}
    current: str | None = None
    in_env_vars = False
    for line in _clean_lines():
        match = _FIELD_RE.match(line)
        if not match:
            continue
        indent = len(match.group("indent"))
        key = match.group("key")
        value = (match.group("value") or "").strip().strip("'\"")
        if key == "envVars" and indent == 4:
            in_env_vars = True
            continue
        if not in_env_vars:
            continue
        if indent <= 4:
            in_env_vars = False
            continue
        if indent == 6 and key == "key":
            current = value
            entries[current] = {}
        elif indent == 8 and current is not None:
            entries[current][key] = value
    return entries


def test_render_manifest_contract() -> None:
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    fields = _service_fields()
    env = _env_vars()

    # Servicio web y región coincidente con Neon (aws-us-east-2 = Ohio).
    assert fields.get("type") == "web", "render.yaml debe declarar un servicio web"
    assert fields.get("runtime") == "python", "runtime debe ser python"
    assert fields.get("region") == "ohio", "la región de Render debe ser ohio (RNF-3)"
    assert fields.get("plan") == "free", "el plan debe ser free (RNF-1)"
    assert fields.get("healthCheckPath") == "/", "healthCheckPath debe ser /"
    assert fields.get("buildCommand") == "pip install -r requirements.txt"
    assert fields.get("startCommand") == "gunicorn app:app"

    # Ejecución y persistencia (D11).
    assert env.get("PYTHON_VERSION", {}).get("value") == "3.12.7"
    assert env.get("SECRET_KEY", {}).get("generateValue") == "true"

    # DATABASE_URL es un secreto: se pide en el panel y no lleva valor.
    database_url = env.get("DATABASE_URL")
    assert database_url is not None, "falta DATABASE_URL en envVars"
    assert database_url.get("sync") == "false", "DATABASE_URL debe usar sync: false"
    assert "value" not in database_url, "DATABASE_URL no debe versionar un valor"
    assert "generateValue" not in database_url, (
        "DATABASE_URL no se genera: debe configurarse como secreto en Render"
    )

    # El almacenamiento SQLite de rollback no se declara en producción.
    assert "PERSISTENCE_BACKEND" not in env, (
        "PERSISTENCE_BACKEND no debe estar en render.yaml"
    )
    assert "PERSISTENCE_BACKEND" not in text
    assert "DATABASE_PATH" not in env, "DATABASE_PATH no debe estar en render.yaml"
    assert "DATABASE_PATH" not in text

    # Sin DSN, credenciales ni material secreto en el manifiesto.
    lowered = text.lower()
    for forbidden in (
        "postgresql://",
        "postgres://",
        "neon.tech",
        "sslmode=",
        "password",
        "api_key",
    ):
        assert forbidden not in lowered, f"render.yaml no debe contener {forbidden!r}"
