# -*- coding: utf-8 -*-

import base64
import io
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    _logger.warning('openpyxl library not found. Please install it with: pip install openpyxl')
    openpyxl = None


class ImportProductsWizard(models.TransientModel):
    _name = 'import.products.wizard'
    _description = 'Wizard para importar productos desde Excel'

    file = fields.Binary(
        string='Archivo Excel',
        required=True,
        help='Seleccione el archivo Excel con los datos de los productos'
    )
    filename = fields.Char(string='Nombre del archivo')

    import_log = fields.Text(
        string='Log de Importación',
        readonly=True,
        help='Registro de las acciones realizadas durante la importación'
    )

    def _get_cell_value(self, row, index):
        try:
            if len(row) > index and row[index] is not None:
                value = row[index]
                if isinstance(value, str):
                    return value.strip()
                return str(value).strip() if value else ''
            return ''
        except:
            return ''

    def action_import_products(self):
        self.ensure_one()

        if not self.file:
            raise UserError(_('Por favor, seleccione un archivo Excel para importar.'))

        if not openpyxl:
            raise UserError(_('Falta la librería openpyxl. Por favor, instálala con: pip install openpyxl'))

        try:
            file_content = base64.b64decode(self.file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
            sheet = workbook.active

            log_messages = []
            created_count = 0
            updated_count = 0
            error_count = 0

            Product = self.env['product.product']
            ProductTmpl = self.env['product.template']
            Category = self.env['product.category']
            StockQuant = self.env['stock.quant']

            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    # Mostrar la fila para depuración
                    print(f"Fila {row_num}: {row}")
                    log_messages.append(f"Fila {row_num} datos: {row}")

                    name = self._get_cell_value(row, 1)  # Columna 1: Nombre
                    pvp = self._get_cell_value(row, 2)   # Columna 2: PVP
                    category_name = self._get_cell_value(row, 3)  # Columna 3: Categoría
                    stock = self._get_cell_value(row, 4)  # Columna 4: Existencias
                    alquiler = self._get_cell_value(row, 5)  # Columna 5: Precio alquiler

                    # Saltar cabecera si detecta texto en PVP
                    try:
                        float(pvp) if pvp else 0.0
                    except Exception:
                        log_messages.append(f'Fila {row_num}: Saltada (posible cabecera o columna PVP no numérica)')
                        continue

                    if not name:
                        log_messages.append(f'Fila {row_num}: Saltada - No hay nombre de producto')
                        continue

                    # Buscar o crear categoría
                    category = Category.search([('name', '=', category_name)], limit=1)
                    if not category:
                        category = Category.create({'name': category_name})
                        log_messages.append(f'  └─ Categoría creada: {category_name}')

                    # Buscar producto por nombre y categoría
                    product = Product.search([
                        ('name', '=', name),
                        ('categ_id', '=', category.id)
                    ], limit=1)

                    vals = {
                        'name': name,
                        'categ_id': category.id,
                        'list_price': float(pvp) if pvp else 0.0,
                        'alquiler_price': float(alquiler) if alquiler else 0.0,
                        'qty_available': float(stock) if stock else 0.0,
                        'is_storable': 'True',  # Rastrear inventario
                        'rent_ok': True,  # Campo para marcar como producto de alquiler
                    }

                    # Si el campo alquiler_price no existe, ignóralo
                    if 'alquiler_price' not in ProductTmpl._fields:
                        vals.pop('alquiler_price', None)
                    if 'alquiler_ok' not in ProductTmpl._fields:
                        vals.pop('alquiler_ok', None)
                    if 'tracking' not in ProductTmpl._fields:
                        vals.pop('tracking', None)

                    if product:
                        product.write(vals)
                        updated_count += 1
                        log_messages.append(f'Fila {row_num}: Producto "{name}" actualizado')
                    else:
                        # Crear producto
                        tmpl = ProductTmpl.create(vals)
                        product = tmpl.product_variant_id
                        created_count += 1
                        log_messages.append(f'Fila {row_num}: Producto "{name}" creado')

                    # Actualizar existencias si hay stock y el producto tiene tipo almacenable
                    if stock and product.product_tmpl_id.type == 'product':
                        try:
                            stock_val = float(stock)
                            # Buscar quants existentes
                            quants = StockQuant.search([
                                ('product_id', '=', product.id),
                                ('location_id.usage', '=', 'internal')
                            ], limit=1)
                            if quants:
                                quants.write({'quantity': stock_val})
                            else:
                                # Buscar ubicación principal
                                location = self.env['stock.location'].search([
                                    ('usage', '=', 'internal')
                                ], limit=1)
                                if location:
                                    StockQuant.create({
                                        'product_id': product.id,
                                        'location_id': location.id,
                                        'quantity': stock_val
                                    })
                            log_messages.append(f'  └─ Stock actualizado: {stock_val}')
                        except Exception as e:
                            log_messages.append(f'  └─ Error actualizando stock: {str(e)}')

                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    log_messages.append(f'Fila {row_num}: ERROR - {error_msg}')
                    _logger.error(f'Error procesando fila {row_num}: {error_msg}')

            summary = f"""
RESUMEN DE IMPORTACIÓN
{'='*50}
✓ Productos creados: {created_count}
✓ Productos actualizados: {updated_count}
✗ Errores: {error_count}

DETALLE:
{'='*50}
{chr(10).join(log_messages)}
            """

            self.import_log = summary

            return {
                'name': _('Resultado de la Importación'),
                'type': 'ir.actions.act_window',
                'res_model': 'import.products.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {'show_log': True}
            }

        except Exception as e:
            raise UserError(_(f'Error al procesar el archivo: {str(e)}'))
