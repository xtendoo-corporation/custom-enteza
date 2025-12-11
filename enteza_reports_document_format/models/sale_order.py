# -*- coding: utf-8 -*-
# Copyright 2021 - Daniel Domínguez https://xtendoo.es/
# Copyright 2025 - Xtendoo - Migrated to Odoo 19

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    event_date = fields.Date(
        string="Fecha Evento",
    )

    @api.depends("order_line.product_id.categ_id")
    def _compute_used_categories(self):
        for order in self:
            categories = order.order_line.filtered(
                lambda l: l.product_id and l.product_id.categ_id
            ).mapped("product_id.categ_id")
            order.used_categories = categories

    used_categories = fields.Many2many(
        comodel_name="product.category",
        string="Categorías",
        compute="_compute_used_categories",
        store=False,
    )

