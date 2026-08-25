# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable de venta',
        index=True,
        help='Usuario responsable de ventas para este contacto',
    )

