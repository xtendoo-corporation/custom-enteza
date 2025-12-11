# -*- coding: utf-8 -*-
# Copyright 2021 - Abraham Carrasco https://xtendoo.es/
# Copyright 2025 - Xtendoo - Migrated to Odoo 19

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    client_id = fields.Many2one(
        comodel_name="res.partner",
        related="sale_id.partner_id",
        string="Cliente",
        store=True,
    )

    @api.depends("move_ids.product_id.categ_id")
    def _compute_stock_used_categories(self):
        for stock in self:
            categories = stock.move_ids.filtered(
                lambda l: l.product_id and l.product_id.categ_id
            ).mapped("product_id.categ_id")
            stock.stock_used_categories = categories

    stock_used_categories = fields.Many2many(
        comodel_name="product.category",
        string="Categorías",
        compute="_compute_stock_used_categories",
        store=False,
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        related="product_id.categ_id",
        string="Categoría",
        store=True,
    )


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        related="product_id.categ_id",
        string="Categoría",
        store=True,
    )

