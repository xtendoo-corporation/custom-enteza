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
            StockPicking = self.env['stock.picking']
            StockPickingType = self.env['stock.picking.type']

            pricelist = Pricelist.search([('active', '=', True)], limit=1)

            for origin, order_data in orders_dict.items():
                try:
                    partner = self._find_partner_by_name(order_data['customer_name'])
                    if not partner:
                        log_messages.append(f'  └─ Cliente NO encontrado: {order_data["customer_name"]} (pedido {origin})')
                        continue

                    order_vals = {
                        'partner_id': partner.id,
                        'pricelist_id': pricelist.id if pricelist else False,
                        'origin': origin,
                        'date_order': fields.Datetime.now(),
                        'rental_start_date': order_data['date_start'],
                        'rental_return_date': order_data['date_end'],
                        'is_rental_order': True,
                    }
                    order = RentalOrder.create(order_vals)
                    # Crear líneas antes de confirmar
                    lines_created = 0
                    picking_products = []
                    for line in order_data['lines']:
                        product = Product.search([('name', '=', line['product_name'])], limit=1)
                        if not product:
                            log_messages.append(f'  └─ Producto no encontrado: {line["product_name"]} (pedido {origin})')
                            continue
                        line_vals = {
                            'order_id': order.id,
                            'product_id': product.id,
                            'product_uom_qty': float(line['qty']),
                            'price_unit': float(line['price']) if line['price'] else product.list_price,
                            'tax_ids': [(6, 0, [])],
                        }
                        if line['iva']:
                            try:
                                tax_amount = float(line['iva'].replace('%','').replace('IVA','').strip())
                                tax = self.env['account.tax'].search([('amount', '=', tax_amount), ('type_tax_use', '=', 'sale')], limit=1)
                                if tax:
                                    line_vals['tax_ids'] = [(6, 0, [tax.id])]
                            except Exception as e:
                                log_messages.append(f'  └─ Error interpretando IVA: {line["iva"]} (pedido {origin})')
                        RentalOrderLine.create(line_vals)
                        lines_created += 1
                        picking_products.append((product, float(line['qty'])))
                    # Confirmar el pedido automáticamente
                    order.action_confirm()
                    # Crear y programar la entrega (picking de salida) y la recogida (picking de entrada)
                    for picking in order.picking_ids:
                        if picking.picking_type_code == 'outgoing':
                            picking.scheduled_date = order.rental_start_date
                            picking.date_deadline = order.rental_start_date
                            picking.write({
                                'scheduled_date': order.rental_start_date,
                                'date_deadline': order.rental_start_date,
                            })
                            _logger.info(f"[FECHA] Entrega: {picking.name} - scheduled_date={picking.scheduled_date} (esperado: {order.rental_start_date})")
                        elif picking.picking_type_code == 'incoming':
                            picking.scheduled_date = order.rental_return_date
                            picking.date_deadline = order.rental_return_date
                            picking.write({
                                'scheduled_date': order.rental_return_date,
                                'date_deadline': order.rental_return_date,
                            })
                            _logger.info(f"[FECHA] Recogida: {picking.name} - scheduled_date={picking.scheduled_date} (esperado: {order.rental_return_date})")
                    # Si no existe recogida, crearla manualmente
                    has_incoming = any(p.picking_type_code == 'incoming' for p in order.picking_ids)
                    if not has_incoming:
                        incoming_type = StockPickingType.search([('code', '=', 'incoming')], limit=1)
                        if incoming_type:
                            picking_vals = {
                                'partner_id': partner.id,
                                'picking_type_id': incoming_type.id,
                                'origin': order.name,
                                'scheduled_date': order.rental_return_date,
                                'date_deadline': order.rental_return_date,
                                'location_id': incoming_type.default_location_src_id.id,
                                'location_dest_id': incoming_type.default_location_dest_id.id,
                                'company_id': order.company_id.id,
                            }
                            if hasattr(StockPicking, 'sale_id'):
                                picking_vals['sale_id'] = order.id
                            picking = StockPicking.create(picking_vals)
                            _logger.info(f"[FECHA] Recogida manual: {picking.name} - scheduled_date={picking.scheduled_date} (esperado: {order.rental_return_date})")
                            move_model = self.env['stock.move']
                            for product, qty in picking_products:
                                move_vals = {
                                    'product_id': product.id,
                                    'product_uom_qty': qty,
                                    'product_uom': product.uom_id.id,
                                    'location_id': incoming_type.default_location_src_id.id,
                                    'location_dest_id': incoming_type.default_location_dest_id.id,
                                    'company_id': order.company_id.id,
                                    'picking_id': picking.id,
                                    'state': 'draft',
                                }
                                sale_line = self.env['sale.order.line'].search([
                                    ('order_id', '=', order.id),
                                    ('product_id', '=', product.id)
                                ], limit=1)
                                move_vals['sale_line_id'] = sale_line.id if sale_line else False
                                move = move_model.create(move_vals)
                                move._action_confirm()
                            if hasattr(picking, '_compute_sale_id'):
                                picking._compute_sale_id()
                            else:
                                picking.write({})
                            picking.action_confirm()
                            picking.action_assign()
                            # Asignar la fecha de recogida después de confirmar y asignar
                            picking.write({
                                'scheduled_date': order.rental_return_date,
                                'date_deadline': order.rental_return_date,
                            })
                            _logger.info(f"[FECHA] Recogida manual confirmada: {picking.name} - scheduled_date={picking.scheduled_date} (esperado: {order.rental_return_date})")
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
