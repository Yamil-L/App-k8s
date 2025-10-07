#!/bin/bash

echo "Generando carga en el backend..."
echo "Presiona Ctrl+C para detener"

# Hacer muchas peticiones en paralelo
for i in {1..100}; do
  (
    while true; do
      curl -X POST http://localhost:8000/api/process \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"Test load $i - $(date)\", \"service\": \"translate\", \"options\": {}}" \
        -s -o /dev/null &
      sleep 0.1
    done
  ) &
done

wait
