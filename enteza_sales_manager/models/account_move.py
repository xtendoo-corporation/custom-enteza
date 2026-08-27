# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable de venta',
        compute='_compute_sale_responsible',
        inverse='_inverse_sale_responsible',
        store=True,
        index=True,
        help='Usuario responsable de ventas vinculado al cliente de la factura',
    )

    @api.depends('partner_id', 'partner_id.sale_responsible_id')
    def _compute_sale_responsible(self):
        for move in self:
            move.sale_responsible_id = move.partner_id.sale_responsible_id if move.partner_id else False

    def _inverse_sale_responsible(self):
        # Si se modifica en la factura, propagar al partner (opcional)
        for move in self:
            if move.partner_id and move.sale_responsible_id:
                try:
                    move.partner_id.sale_responsible_id = move.sale_responsible_id
                except Exception:
                    # no romper si el partner no es escribible por permisos
                    pass


