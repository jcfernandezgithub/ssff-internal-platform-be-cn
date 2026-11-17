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

# Tarifas de referencia en USD por cada 1.000.000 de tokens (input / output)
TARIFAS_TOKENS_1M: dict[str, tuple[float, float]] = {
    "gemini-3.5-flash": (0.30, 2.50),
    "gemini-3-flash": (0.30, 2.50),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.1-flash-image": (0.50, 60.00),
    "gemini-3-pro-image": (2.00, 120.00),
}
TARIFA_DEFAULT_1M: tuple[float, float] = (0.30, 2.50)


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


def _calcular_costo_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calcula el costo en USD según el modelo y los tokens consumidos."""
    modelo_norm = (model or "").strip().lower()
    tarifa = TARIFAS_TOKENS_1M.get(modelo_norm)

    if tarifa is None:
        # Coincidencia por prefijo para variantes con sufijo de versión (ej. -001, -preview)
        for clave, valores in TARIFAS_TOKENS_1M.items():
            if modelo_norm.startswith(clave):
                tarifa = valores
                break

    input_rate, output_rate = tarifa or TARIFA_DEFAULT_1M
    costo = ((prompt_tokens / 1_000_000) * input_rate) + (
        (completion_tokens / 1_000_000) * output_rate
    )
    return round(costo, 6)


def registrar_consumo_gemini(
    response: Any,
    *,
    model: str,
    agent_id: str | None = None,
    product: str | None = None,
) -> bool:
    """Registra los tokens y el costo USD sin interrumpir el procesamiento."""
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

        prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        candidates_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        thoughts_tokens = int(getattr(usage, "thoughts_token_count", 0) or 0)
        total_tokens = int(getattr(usage, "total_token_count", 0) or 0)

        # Los tokens de razonamiento (thoughts) se facturan como tokens de salida
        completion_tokens = candidates_tokens + thoughts_tokens
        if total_tokens > (prompt_tokens + completion_tokens) and thoughts_tokens == 0:
            completion_tokens = total_tokens - prompt_tokens
        if total_tokens < (prompt_tokens + completion_tokens):
            total_tokens = prompt_tokens + completion_tokens

        cost_usd = _calcular_costo_usd(model, prompt_tokens, completion_tokens)

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id
            or os.getenv("BIGQUERY_AUDIT_AGENT_ID", "Cambio_de_Nombre"),
            "product": product
            or os.getenv("BIGQUERY_AUDIT_PRODUCT", "FORJA"),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "unit_type": "tokens",
            "cost_usd": cost_usd,
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
            f"para agent_id='{row['agent_id']}' | costo=${cost_usd:.6f} USD."
        )
        return True
    except Exception as exc:
        # La auditoría es secundaria y nunca debe detener el flujo productivo.
        print(f"[BigQuery Audit] Registro omitido por error: {exc}")
        return False