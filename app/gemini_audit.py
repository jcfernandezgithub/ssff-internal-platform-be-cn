"""Auditoría best-effort del consumo de Gemini en BigQuery.

Este módulo nunca propaga errores al flujo principal. La auditoría se activa
únicamente cuando BIGQUERY_AUDIT_ENABLED=true.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any


_client: Any | None = None
_client_lock = threading.Lock()


def _is_enabled() -> bool:
    return os.getenv("BIGQUERY_AUDIT_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_client() -> Any:
    """Crea el cliente de forma diferida para no afectar el arranque."""
    global _client

    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        from google.cloud import bigquery

        project_id = os.environ["BIGQUERY_PROJECT_ID"]
        credentials_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")

        if credentials_json:
            from google.oauth2 import service_account

            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info
            )
            _client = bigquery.Client(
                project=project_id,
                credentials=credentials,
            )
        else:
            # Permite utilizar ADC en desarrollo o si el hosting lo provee.
            _client = bigquery.Client(project=project_id)

        return _client


def registrar_consumo_gemini(
    response: Any,
    *,
    model: str,
    agent_id: str | None = None,
    product: str | None = None,
) -> bool:
    """Registra los tokens de una respuesta sin interrumpir el procesamiento."""
    if not _is_enabled():
        return False

    try:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            print("[BigQuery Audit] Gemini no devolvió usage_metadata; se omite el registro.")
            return False

        project_id = os.environ["BIGQUERY_PROJECT_ID"]
        dataset_id = os.getenv("BIGQUERY_DATASET_ID", "audit_ia")
        table_id = os.getenv("BIGQUERY_TABLE_ID", "gemini_tokens")
        table_ref = f"{project_id}.{dataset_id}.{table_id}"

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id
            or os.getenv("BIGQUERY_AUDIT_AGENT_ID", "SSFF_Cambio_Nombre"),
            "product": product
            or os.getenv("BIGQUERY_AUDIT_PRODUCT", "SSFF_Internal_Platform"),
            "model": model,
            "prompt_tokens": int(getattr(usage, "prompt_token_count", 0) or 0),
            "completion_tokens": int(
                getattr(usage, "candidates_token_count", 0) or 0
            ),
            "total_tokens": int(getattr(usage, "total_token_count", 0) or 0),
        }

        errors = _get_client().insert_rows_json(
            table_ref,
            [row],
            timeout=5.0,
        )
        if errors:
            print(f"[BigQuery Audit] Inserción rechazada: {errors}")
            return False

        print(
            "[BigQuery Audit] Consumo registrado "
            f"para agent_id='{row['agent_id']}'."
        )
        return True
    except Exception as exc:
        # La auditoría es secundaria y nunca debe detener el flujo productivo.
        print(f"[BigQuery Audit] Registro omitido por error: {exc}")
        return False
