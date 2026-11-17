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

## Alcance y verificación

La única llamada activa a `generate_content` en `app/procesar.py` invoca la
auditoría inmediatamente después de recibir la respuesta y antes de leer su texto.
Por tanto, una respuesta que después falle al interpretarse como JSON también
intenta registrar su consumo.

El registro es **best-effort**: si faltan metadatos, hay errores de credenciales
o BigQuery rechaza la inserción, se escribe un log y se continúa. No existe una
cola persistente para recuperar registros fallidos. Esto no garantiza una fila
por cada consumo ante fallos. `agent_id` identifica el servicio configurado;
no identifica al usuario final autenticado.

Pruebas locales con cliente simulado (sin consumir tokens ni insertar filas):

```sh
python3 -B -m unittest discover -s tests -v
```

Para verificar producción, procesar una URL y contrastar los logs con las filas
recientes del producto configurado:

```sql
SELECT timestamp, agent_id, product, model,
       prompt_tokens, completion_tokens, total_tokens
FROM `poc-ia-growth-y-productos.audit_ia.gemini_tokens`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND product = 'SSFF_Internal_Platform'
ORDER BY timestamp DESC
LIMIT 100;
```

La credencial de ejecución debe tener permiso para insertar en esa tabla.
La cuenta usada para esta consulta necesita además permisos de lectura y
ejecución de consultas. Las pruebas simuladas no validan esos permisos, el
esquema real, las variables del despliegue ni la disponibilidad del modelo.
