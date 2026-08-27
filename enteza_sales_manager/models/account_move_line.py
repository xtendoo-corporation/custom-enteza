# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable de venta',
        compute='_compute_sale_responsible',
        inverse='_inverse_sale_responsible',
        store=True,
        index=True,
        help='Usuario responsable de ventas vinculado al cliente de la línea contable.',
    )

    @api.depends('partner_id', 'partner_id.sale_responsible_id')
    def _compute_sale_responsible(self):
        for line in self:
            line.sale_responsible_id = line.partner_id.sale_responsible_id if line.partner_id else False

    def _inverse_sale_responsible(self):
        for line in self:
            if line.partner_id and line.sale_responsible_id:
                try:
                    line.partner_id.sale_responsible_id = line.sale_responsible_id
                except Exception:
                    pass




