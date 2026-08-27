# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable de venta',
        related='partner_id.sale_responsible_id',
        store=True,
        index=True,
        readonly=False,
        help='Usuario responsable de ventas heredado del asiento/factura.',
    )




