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


class ImportCustomersWizard(models.TransientModel):
    _name = 'import.customers.wizard'
    _description = 'Wizard para importar clientes desde Excel'

    file = fields.Binary(
        string='Archivo Excel',
        required=True,
        help='Seleccione el archivo Excel con los datos de los clientes'
    )
    filename = fields.Char(string='Nombre del archivo')

    import_log = fields.Text(
        string='Log de Importación',
        readonly=True,
        help='Registro de las acciones realizadas durante la importación'
    )

    def _get_cell_value(self, row, index):
        """Obtiene el valor de una celda específica por índice, manejando valores vacíos"""
        try:
            if len(row) > index and row[index] is not None:
                value = row[index]
                if isinstance(value, str):
                    return value.strip()
                return str(value).strip() if value else ''
            return ''
        except:
            return ''

    def _clean_phone_number(self, phone_value):
        """Limpia el número de teléfono eliminando el apóstrofo inicial que Excel añade"""
        if not phone_value:
            return ''
        phone_str = str(phone_value).strip()
        # Eliminar apóstrofo inicial si existe
        if phone_str.startswith("'"):
            phone_str = phone_str[1:]
        return phone_str.strip()

    def _is_numeric(self, value):
        """Verifica si un valor es numérico"""
        if not value:
            return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _create_or_update_address(self, partner, address_data, address_type):
        """Crea o actualiza una dirección para un contacto"""
        if not address_data.get('street'):
            return None

        # Buscar si ya existe una dirección similar
        existing_address = self.env['res.partner'].search([
            ('parent_id', '=', partner.id),
            ('type', '=', address_type),
            ('street', '=', address_data.get('street')),
        ], limit=1)

        if existing_address:
            existing_address.write(address_data)
            return existing_address
        else:
            address_data['parent_id'] = partner.id
            address_data['type'] = address_type
            return self.env['res.partner'].create(address_data)

    def _get_partner_phone_fields(self):
        """Detecta si el modelo res.partner tiene el campo 'mobile'."""
        partner_fields = self.env['res.partner'].fields_get()
        has_mobile = 'mobile' in partner_fields
        return has_mobile

    def action_import_customers(self):
        """Procesa el archivo Excel e importa los clientes"""
        self.ensure_one()

        if not self.file:
            raise UserError(_('Por favor, seleccione un archivo Excel para importar.'))

        if not openpyxl:
            raise UserError(_('Falta la librería openpyxl. Por favor, instálala con: pip install openpyxl'))

        try:
            # Decodificar el archivo
            file_content = base64.b64decode(self.file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
            sheet = workbook.active

            log_messages = []
            created_count = 0
            updated_count = 0
            error_count = 0

            has_mobile = self._get_partner_phone_fields()

            # Iterar sobre las filas (empezando desde la fila 2 para saltar encabezados)
            # values_only=True devuelve una tupla con los valores directamente
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    # Mapeo de columnas según el requerimiento:
                    # B=1, C=2, F=5, G=6, H=7, I=8, J=9, L=11, Q=16, S=18, Y=24, Z=25
                    name = self._get_cell_value(row, 1)  # Columna B (índice 1)
                    street = self._get_cell_value(row, 2)  # Columna C (índice 2)
                    zip_code = self._get_cell_value(row, 5)  # Columna F (índice 5)
                    city = self._get_cell_value(row, 6)  # Columna G (índice 6)
                    state = self._get_cell_value(row, 7)  # Columna H (índice 7)
                    phone = self._clean_phone_number(self._get_cell_value(row, 8))  # Columna I (índice 8)
                    phone2 = self._clean_phone_number(self._get_cell_value(row, 9))  # Columna J (índice 9)
                    invoice_street = self._get_cell_value(row, 11)  # Columna L (índice 11)
                    ref = self._get_cell_value(row, 16)  # Columna Q (índice 16)
                    email = self._get_cell_value(row, 18)  # Columna S (índice 18)
                    description_y = self._get_cell_value(row, 24)  # Columna Y (índice 24)
                    description_z = self._get_cell_value(row, 25)  # Columna Z (índice 25)

                    # Debug: Imprimir valores leídos
                    print(f"Fila {row_num}: name='{name}', street='{street}', ref='{ref}'")

                    # Validar que al menos haya un nombre
                    if not name:
                        log_messages.append(f'Fila {row_num}: Saltada - No hay nombre')
                        continue

                    # Si todos los campos están vacíos, detener la importación
                    if not any([name, street, zip_code, city, phone, email, ref]):
                        print(f"Fila {row_num}: Todos los datos están vacíos. Terminando la importación.")
                        break

                    # Preparar datos del contacto principal
                    if has_mobile:
                        partner_vals = {
                            'name': name,
                            'street': street if street else False,
                            'zip': zip_code if zip_code else False,
                            'city': city if city else False,
                            'phone': phone if phone else False,
                            'mobile': phone2 if phone2 else False,
                            'email': email if email else False,
                            'ref': ref if ref else False,
                            'is_company': True,
                            'lang': 'es_ES',
                        }
                    else:
                        # Si no existe 'mobile', concatenar ambos teléfonos en 'phone'
                        phone_concat = phone
                        if phone2:
                            phone_concat = f"{phone} - {phone2}" if phone else phone2
                        partner_vals = {
                            'name': name,
                            'street': street if street else False,
                            'zip': zip_code if zip_code else False,
                            'city': city if city else False,
                            'phone': phone_concat if phone_concat else False,
                            'email': email if email else False,
                            'ref': ref if ref else False,
                            'is_company': True,
                            'lang': 'es_ES',
                        }

                    # Manejar estado (solo si no es numérico)
                    if state and not self._is_numeric(state):
                        # Buscar el estado por nombre
                        state_obj = self.env['res.country.state'].search([
                            ('name', 'ilike', state)
                        ], limit=1)
                        if state_obj:
                            partner_vals['state_id'] = state_obj.id

                    # Manejar descripciones
                    comment_parts = []
                    if description_y and description_y.lower() not in ['falso', 'false', '']:
                        # Si description_y es verdadero, poner el texto requerido
                        comment_parts.append('Requiere factura anticipada, ')
                    if description_z:
                        comment_parts.append(description_z)
                    if comment_parts:
                        partner_vals['comment'] = '\n'.join(comment_parts)

                    # Buscar si el contacto ya existe (por nombre o referencia)
                    domain = []
                    if ref:
                        domain = ['|', ('name', '=', name), ('ref', '=', ref)]
                    else:
                        domain = [('name', '=', name)]

                    existing_partner = self.env['res.partner'].search(domain, limit=1)

                    if existing_partner:
                        # Actualizar contacto existente
                        existing_partner.write(partner_vals)
                        partner = existing_partner
                        updated_count += 1
                        log_messages.append(f'Fila {row_num}: Cliente "{name}" actualizado')
                    else:
                        # Crear nuevo contacto
                        partner = self.env['res.partner'].create(partner_vals)
                        created_count += 1
                        log_messages.append(f'Fila {row_num}: Cliente "{name}" creado')

                    # Manejar dirección de facturación si es diferente
                    if invoice_street and invoice_street != street and invoice_street.strip():
                        invoice_address_vals = {
                            'name': f"{name} - Facturación",
                            'street': invoice_street,
                            'zip': zip_code if zip_code else False,
                            'city': city if city else False,
                        }
                        if state and not self._is_numeric(state):
                            state_obj = self.env['res.country.state'].search([
                                ('name', 'ilike', state)
                            ], limit=1)
                            if state_obj:
                                invoice_address_vals['state_id'] = state_obj.id

                        self._create_or_update_address(partner, invoice_address_vals, 'invoice')
                        log_messages.append(f'  └─ Dirección de facturación creada/actualizada para "{name}"')

                    # Flush después de cada contacto
                    self.env.cr.flush()

                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    log_messages.append(f'Fila {row_num}: ERROR - {error_msg}')
                    _logger.error(f'Error procesando fila {row_num}: {error_msg}')

            # Preparar mensaje final
            summary = f"""
RESUMEN DE IMPORTACIÓN
{'='*50}
✓ Clientes creados: {created_count}
✓ Clientes actualizados: {updated_count}
✗ Errores: {error_count}

DETALLE:
{'='*50}
{chr(10).join(log_messages)}
            """

            self.import_log = summary

            # Mostrar el resultado
            return {
                'name': _('Resultado de la Importación'),
                'type': 'ir.actions.act_window',
                'res_model': 'import.customers.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {'show_log': True}
            }

        except Exception as e:
            raise UserError(_(f'Error al procesar el archivo: {str(e)}'))
