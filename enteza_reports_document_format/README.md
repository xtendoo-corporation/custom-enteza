# Enteza Reports Document Format

## Descripción

Módulo para Odoo 19 que proporciona formatos de documentos personalizados para reportes de:
- Pedidos de venta
- Albaranes de entrega
- Facturas

Los reportes agrupan las líneas por categorías de producto para una mejor organización y lectura.

## Características

### Pedidos de Venta
- Reporte agrupado por categorías de producto
- Muestra precio de coste (si aplica)
- Campo para fecha de evento
- Información detallada del cliente y direcciones

### Albaranes
- Reporte agrupado por categorías de producto
- Muestra cliente y fecha del evento
- Información de cantidades pedidas y entregadas
- Soporte para backorders

### Facturas
- Reporte agrupado por categorías de producto
- Campo adicional para fecha de evento
- Agrupación por secciones de líneas

## Dependencias

- base
- sale
- stock
- sale_management
- account

## Instalación

1. Copiar el módulo en la carpeta de addons personalizada
2. Actualizar la lista de módulos
3. Instalar el módulo "Enteza Reports Document Format"

## Uso

Una vez instalado, los nuevos reportes estarán disponibles en:
- Pedidos de venta: "Pedido/Presupuesto Agrupado"
- Albaranes: "Albarán Agrupado"
- Facturas: "Factura Agrupada"

## Migración desde Odoo 15

Este módulo ha sido migrado desde `visuena_document_format` (Odoo 15) a Odoo 19.

Principales cambios en la migración:
- Actualización de la versión del manifest a 19.0.1.0.0
- Adaptación de vistas XML a la nueva sintaxis de Odoo 19
- Actualización de campos computados para usar sintaxis moderna
- Cambio de `t-esc` a `t-out` en templates QWeb
- Actualización de clases CSS de Bootstrap (ml-auto → ms-auto, mr-16 → me-3, etc.)
- Actualización del campo `tax_totals_json` a `tax_totals`
- Corrección de referencias a campos deprecados
- Actualización de métodos de stock (`move_lines` → `move_ids_without_package`)

## Autor

- Dani Domínguez
- Manuel Calero
- Abraham Carrasco

**Xtendoo** - https://www.xtendoo.es

## Licencia

AGPL-3

