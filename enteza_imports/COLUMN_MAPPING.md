# Estructura del Excel para Importación de Clientes

## Mapeo de Columnas

El wizard lee las columnas del Excel usando la siguiente estructura:

| Letra | Posición | Índice | Campo en Odoo | Descripción |
|-------|----------|--------|---------------|-------------|
| A | 1 | 0 | - | (No se usa) |
| **B** | **2** | **1** | **name** | **Nombre del cliente (REQUERIDO)** |
| **C** | **3** | **2** | **street** | **Dirección principal** |
| D | 4 | 3 | - | (No se usa) |
| E | 5 | 4 | - | (No se usa) |
| **F** | **6** | **5** | **zip** | **Código Postal** |
| **G** | **7** | **6** | **city** | **Ciudad** |
| **H** | **8** | **7** | **state_id** | **Estado/Provincia** (se ignora si es numérico) |
| **I** | **9** | **8** | **phone** | **Teléfono** |
| **J** | **10** | **9** | **mobile** | **Teléfono 2/Móvil** |
| K | 11 | 10 | - | (No se usa) |
| **L** | **12** | **11** | **invoice_address** | **Dirección de facturación** (crea contacto hijo si es diferente a C) |
| M-P | 13-16 | 12-15 | - | (No se usa) |
| **Q** | **17** | **16** | **ref** | **Referencia interna** |
| R | 18 | 17 | - | (No se usa) |
| **S** | **19** | **18** | **email** | **Email** |
| T-X | 20-24 | 19-23 | - | (No se usa) |
| **Y** | **25** | **24** | **comment** | **Descripción 1** (solo si no es "falso") |
| **Z** | **26** | **25** | **comment** | **Descripción 2** |

## Ejemplo de Estructura

```
| A | B (name) | C (street) | D | E | F (zip) | G (city) | H (state) | I (phone) | J (mobile) | K | L (invoice_street) | ... | Q (ref) | R | S (email) | ... | Y (desc1) | Z (desc2) |
|---|----------|------------|---|---|---------|----------|-----------|-----------|------------|---|--------------------|-----|---------|---|-----------|-----|-----------|-----------|
| 1 | Cliente A| Calle 1    |   |   | 28001   | Madrid   | Madrid    | 912345678 | 600123456  |   | Calle Factura 1    | ... | REF001  |   | mail@x.com| ... | Nota 1    | Nota 2    |
| 2 | Cliente B| Calle 2    |   |   | 08001   | Barcelona| Barcelona | 932345678 |            |   |                    | ... |         |   | info@y.com| ... |           | Observ.   |
```

## Notas Importantes

1. **La columna B (nombre) es obligatoria**. Si está vacía, la fila se salta.
2. **La primera fila se ignora** (se asume que son encabezados).
3. **Las columnas se leen por índice**, no por nombre de columna.
4. **Estados numéricos se ignoran automáticamente**.
5. **Si la columna L (dirección facturación) es diferente a la C (dirección), se crea un contacto hijo** de tipo "Dirección de facturación".
6. **Las descripciones Y y Z se concatenan** en el campo "Notas internas" del contacto.
7. **Si Y contiene "falso" o "false", no se guarda**.

## Proceso de Importación

1. El wizard lee el archivo Excel fila por fila
2. Por cada fila:
   - Verifica que haya un nombre (columna B)
   - Busca si existe un contacto con ese nombre o referencia
   - Si existe: actualiza los datos
   - Si no existe: crea un nuevo contacto
   - Si la dirección de facturación es diferente: crea un contacto hijo
3. Genera un log detallado con:
   - Clientes creados
   - Clientes actualizados
   - Errores encontrados
   - Detalle línea por línea

