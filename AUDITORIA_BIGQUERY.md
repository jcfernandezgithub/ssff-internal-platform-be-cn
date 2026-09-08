# Auditoría de consumo de Gemini en BigQuery

La integración registra una fila después de cada llamada exitosa a Gemini.
Los errores de configuración, credenciales o inserción se registran en logs,
pero no interrumpen el procesamiento ni modifican sus resultados.

## Variables de entorno en Railway

```text
BIGQUERY_AUDIT_ENABLED=true
BIGQUERY_PROJECT_ID=poc-ia-growth-y-productos
BIGQUERY_DATASET_ID=audit_ia
BIGQUERY_TABLE_ID=gemini_tokens
BIGQUERY_AUDIT_AGENT_ID=SSFF_Cambio_Nombre
BIGQUERY_AUDIT_PRODUCT=SSFF_Internal_Platform
GCP_SERVICE_ACCOUNT_JSON={contenido completo del JSON de la cuenta de servicio}
```

`GCP_SERVICE_ACCOUNT_JSON` debe configurarse como secreto en Railway. Nunca debe
guardarse en el repositorio, Dockerfile ni archivos versionados.

La auditoría permanece desactivada si `BIGQUERY_AUDIT_ENABLED` no es `true`.

## Esquema esperado

Tabla: `poc-ia-growth-y-productos.audit_ia.gemini_tokens`

| Campo | Tipo |
| --- | --- |
| timestamp | TIMESTAMP |
| agent_id | STRING |
| product | STRING |
| model | STRING |
| prompt_tokens | INTEGER |
| completion_tokens | INTEGER |
| total_tokens | INTEGER |

## Despliegue seguro

1. Desplegar primero con `BIGQUERY_AUDIT_ENABLED=false` o sin definirla.
2. Ejecutar una prueba funcional y verificar que JSON, CSV y estados no cambian.
3. Configurar las variables de BigQuery y la credencial en Railway.
4. Activar `BIGQUERY_AUDIT_ENABLED=true`.
5. Procesar una URL de prueba.
6. Confirmar en logs el mensaje `[BigQuery Audit] Consumo registrado`.
7. Consultar la tabla y verificar los valores insertados.

## Rollback

Para desactivar la integración sin revertir el despliegue:

```text
BIGQUERY_AUDIT_ENABLED=false
```

El servicio continuará funcionando sin intentar conectarse a BigQuery.
