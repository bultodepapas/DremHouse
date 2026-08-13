# Colaborar con Dream House

Este repositorio es un expediente técnico vivo, no una colección de ideas sueltas.
Toda contribución debe conservar la trazabilidad entre fuente, decisión, hipótesis,
lámina y costo.

## Antes de cambiar algo

1. Lee el [índice del expediente](docs/README.md), la
   [constitución](docs/00_gobernanza/constitucion_del_proyecto.md) y la
   [precedencia documental](docs/00_gobernanza/fuentes_precedencia_y_conflictos.md).
2. Comprueba si el dato es una hard rule, un valor de control, una hipótesis o un
   asunto abierto.
3. No resuelvas una contradicción silenciosamente: registra el conflicto o abre una
   decisión.
4. Si cambia alcance o costo, actualiza la
   [base de costos](docs/04_costos/base_y_control_de_costos.md).

## Flujo recomendado

- Abre una issue de **decisión** para cambios de criterio o una **RFI** para dudas
  técnicas.
- Trabaja en una rama corta y limita cada pull request a un cambio coordinable.
- Declara fuente, fecha, versión, estatus, supuestos y documentos afectados.
- Si emites una lámina, conserva su `manifest.json` y la advertencia de uso.
- Ejecuta la validación de la presentación antes de enviar cambios:

```powershell
python .github/scripts/build_showcase.py --write-readme --site-dir .build/showcase
python .github/scripts/build_showcase.py --check-readme
```

## Criterio de aceptación

Una contribución está lista cuando es trazable, no rompe hard rules, declara sus
incertidumbres, actualiza los documentos afectados y distingue con claridad entre
concepto, coordinación y documento apto para construir.
