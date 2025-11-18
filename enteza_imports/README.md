# Enteza Imports

Módulo de Odoo 19 para importar clientes desde archivos Excel.

## Características

- Importación de clientes desde archivos Excel (.xlsx)
- Wizard intuitivo con interfaz gráfica
- Soporte para múltiples campos de contacto
- Gestión automática de direcciones de facturación diferentes
- Log detallado de importación con resumen de resultados

## Formato del Excel

El archivo Excel debe tener las siguientes columnas (los datos se leen por posición de columna):

- **Columna B (posición 2)**: Nombre del cliente (requerido)
- **Columna C (posición 3)**: Dirección
- **Columna F (posición 6)**: Código Postal
- **Columna G (posición 7)**: Ciudad
- **Columna H (posición 8)**: Estado (se ignora si es numérico)
- **Columna I (posición 9)**: Teléfono
- **Columna J (posición 10)**: Teléfono 2
- **Columna L (posición 12)**: Dirección de facturación (si es diferente a la columna C, se crea una dirección adicional)
- **Columna Q (posición 17)**: Referencia
- **Columna S (posición 19)**: Email
- **Columna Y (posición 25)**: Descripción 1 (solo se guarda si es diferente a "falso")
- **Columna Z (posición 26)**: Descripción 2

**Nota**: La primera fila se considera como encabezados y será ignorada durante la importación.

## Instalación

1. Asegúrese de tener instalada la librería Python `openpyxl`:
   ```bash
   pip install openpyxl
   ```

2. Instale el módulo desde la aplicación Odoo

## Uso

1. Vaya a **Contactos** > **Importar Clientes**
2. Seleccione su archivo Excel
3. Haga clic en **Importar**
4. Revise el log de importación con el resumen de resultados

El wizard mostrará:
- Número de clientes creados
- Número de clientes actualizados
- Número de errores
- Detalle línea por línea de las operaciones realizadas

## Características Avanzadas

- **Detección de duplicados**: Si existe un cliente con el mismo nombre o referencia, se actualiza en lugar de crear uno nuevo
- **Direcciones múltiples**: Si la dirección de facturación (columna L) es diferente a la dirección principal (columna C), se crea automáticamente una dirección de facturación separada
- **Validación de estados**: Los estados numéricos son ignorados automáticamente
- **Manejo de errores**: Los errores en filas individuales no detienen la importación completa

## Versión

- **Versión**: 19.0.1.0.0
- **Compatible con**: Odoo 19.0

