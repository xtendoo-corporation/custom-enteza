# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable de venta',
        compute='_compute_sale_responsible',
        inverse='_inverse_sale_responsible',
        store=True,
        index=True,
        help='Usuario responsable de ventas vinculado al cliente del pedido',
    )

    @api.depends('partner_id', 'partner_id.sale_responsible_id')
    def _compute_sale_responsible(self):
        for order in self:
            order.sale_responsible_id = order.partner_id.sale_responsible_id if order.partner_id else False

    def _inverse_sale_responsible(self):
        for order in self:
            if order.partner_id and order.sale_responsible_id:
                try:
                    order.partner_id.sale_responsible_id = order.sale_responsible_id
                except Exception:
                    pass

