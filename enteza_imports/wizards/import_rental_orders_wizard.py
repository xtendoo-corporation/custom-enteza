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

class ImportRentalOrdersWizard(models.TransientModel):
    _name = 'import.rental.orders.wizard'
    _description = 'Wizard para importar futuros alquileres desde Excel'

    file = fields.Binary(string='Archivo Excel', required=True)
    filename = fields.Char(string='Nombre del archivo')
    import_log = fields.Text(string='Log de Importación', readonly=True)

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

    def _clean_customer_name(self, name):
        # Elimina cualquier número y texto posterior al final del nombre del cliente
        import re
        if not name:
            return ''
        # Quita cualquier secuencia de espacios seguida de números y texto (como " 412087-O") al final
        name = re.sub(r'\s+\d+.*$', '', name)
        # Si hay coma, toma solo la parte antes de la coma
        if ',' in name:
            name = name.split(',')[0].strip()
        return name.strip()

    def _find_partner_by_name(self, name):
        Partner = self.env['res.partner']
        # Búsqueda exacta
        partner = Partner.search([('name', '=', name)], limit=1)
        if partner:
            return partner
        # Búsqueda por similitud fuerte: coincidencia de palabras principales (mínimo 2 palabras iguales)
        partners = Partner.search([])
        name_words = set([w for w in name.lower().replace(',', '').split() if len(w) > 2])
        for p in partners:
            p_name_words = set([w for w in (p.name or '').lower().replace(',', '').split() if len(w) > 2])
            if len(name_words & p_name_words) >= 2:
                return p
        # Búsqueda por similitud débil (todas las palabras del nombre están en el partner)
        for p in partners:
            p_name = (p.name or '').lower().replace(',', '')
            if all(w in p_name for w in name_words):
                return p
        return False

    def action_import_rental_orders(self):
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
            created_orders = 0
            error_count = 0
            orders_dict = {}

            # Leer todas las filas y agrupar por origin
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                origin = self._get_cell_value(row, 0)
                customer_name = self._get_cell_value(row, 1)
                customer_name_clean = self._clean_customer_name(customer_name)
                product_name = self._get_cell_value(row, 3)
                qty = self._get_cell_value(row, 4)
                price = self._get_cell_value(row, 7)  # Columna 7 es el precio
                iva = self._get_cell_value(row, 9)
                date_start = self._get_cell_value(row, 14)
                date_end = self._get_cell_value(row, 15)

                # Normalizar fechas a datetime si son string
                from datetime import datetime, timedelta
                if isinstance(date_start, str):
                    try:
                        date_start = datetime.fromisoformat(date_start)
                    except Exception:
                        try:
                            date_start = datetime.strptime(date_start, '%Y-%m-%d')
                        except Exception:
                            date_start = None
                if isinstance(date_end, str):
                    try:
                        date_end = datetime.fromisoformat(date_end)
                    except Exception:
                        try:
                            date_end = datetime.strptime(date_end, '%Y-%m-%d')
                        except Exception:
                            date_end = None

                # Si alguna fecha no existe, saltar
                if not origin or not customer_name_clean or not product_name or not qty or not date_start:
                    log_messages.append(f'Fila {row_num}: Saltada por datos incompletos')
                    continue

                # Si la fecha de fin es inválida o incoherente, ponerla 2 días después de la de inicio
                if not date_end or date_start >= date_end:
                    date_end = date_start + timedelta(days=2)
                    log_messages.append(f'Fila {row_num}: Fecha de fin ajustada automáticamente a {date_end.date()}')

                if origin not in orders_dict:
                    orders_dict[origin] = {
                        'customer_name': customer_name_clean,
                        'lines': [],
                        'date_start': date_start,
                        'date_end': date_end,
                        'iva': iva,
                    }
                orders_dict[origin]['lines'].append({
                    'product_name': product_name,
                    'qty': qty,
                    'price': price,
                    'iva': iva,
                })

            # Procesar cada pedido
            Product = self.env['product.product']
            Pricelist = self.env['product.pricelist']
            RentalOrder = self.env['sale.order']
            RentalOrderLine = self.env['sale.order.line']

            pricelist = Pricelist.search([('active', '=', True)], limit=1)

            for origin, order_data in orders_dict.items():
                try:
                    partner = self._find_partner_by_name(order_data['customer_name'])
                    if not partner:
                        log_messages.append(f'  └─ Cliente NO encontrado: {order_data["customer_name"]} (pedido {origin})')
                        continue

                    # Crear el pedido con el contexto de alquiler
                    order_vals = {
                        'partner_id': partner.id,
                        'pricelist_id': pricelist.id if pricelist else False,
                        'origin': origin,
                        'date_order': fields.Datetime.now(),
                        'rental_start_date': order_data['date_start'],
                        'rental_return_date': order_data['date_end'],
                        'is_rental_order': True,
                    }
                    order = RentalOrder.with_context(in_rental_app=True).create(order_vals)
                    # Crear líneas antes de confirmar
                    lines_created = 0
                    for line in order_data['lines']:
                        product = Product.search([('name', '=', line['product_name']), ('rent_ok', '=', True)], limit=1)
                        if not product:
                            log_messages.append(f'  └─ Producto no encontrado o no alquilable: {line["product_name"]} (pedido {origin})')
                            continue
                        line_vals = {
                            'order_id': order.id,
                            'product_id': product.id,
                            'product_uom_qty': float(line['qty']),
                            'price_unit': float(line['price']) if line['price'] else product.list_price,
                            'tax_ids': [(6, 0, [])],
                            'is_rental': True,
                        }
                        if line['iva']:
                            try:
                                tax_amount = float(line['iva'].replace('%','').replace('IVA','').strip())
                                tax = self.env['account.tax'].search([('amount', '=', tax_amount), ('type_tax_use', '=', 'sale')], limit=1)
                                if tax:
                                    line_vals['tax_ids'] = [(6, 0, [tax.id])]
                            except Exception as e:
                                log_messages.append(f'  └─ Error interpretando IVA: {line["iva"]} (pedido {origin})')
                        RentalOrderLine.with_context(in_rental_app=True).create(line_vals)
                        lines_created += 1
                    order.action_confirm()
                    created_orders += 1
                    log_messages.append(f'Pedido de alquiler creado y confirmado: {origin} ({lines_created} líneas)')
                except Exception as e:
                    error_count += 1
                    log_messages.append(f'Pedido {origin}: ERROR - {str(e)}')
                    _logger.error(f'Error procesando pedido {origin}: {str(e)}')

            summary = f"""
RESUMEN DE IMPORTACIÓN\n{'='*50}\n✓ Pedidos creados: {created_orders}\n✗ Errores: {error_count}\n\nDETALLE:\n{'='*50}\n{chr(10).join(log_messages)}\n            """
            self.import_log = summary
            return {
                'name': _('Resultado de la Importación'),
                'type': 'ir.actions.act_window',
                'res_model': 'import.rental.orders.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {'show_log': True}
            }
        except Exception as e:
            raise UserError(_(f'Error al procesar el archivo: {str(e)}'))
