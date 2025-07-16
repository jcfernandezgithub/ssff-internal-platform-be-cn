#!/bin/bash

# Ejecutar tu API FastAPI con uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 10000