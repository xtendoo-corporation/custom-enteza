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

    @api.depends("move_line_ids.location_id", "state")
    def _compute_stock_used_locations(self):
        """Calcula las ubicaciones de origen utilizadas en el picking"""
        for picking in self:
            if picking.move_line_ids:
                # Usar location_id directamente de move_line_ids (funciona tanto para done como assigned)
                locations = picking.move_line_ids.mapped("location_id")
            else:
                # Fallback: usar location_id de move_ids si no hay move_line_ids
                locations = picking.move_ids.mapped("location_id")
            picking.stock_used_locations = locations

    stock_used_locations = fields.Many2many(
        comodel_name="stock.location",
        string="Ubicaciones de Origen",
        compute="_compute_stock_used_locations",
        store=False,
    )

    def debug_stock_info(self):
        """Método de depuración para ver información del picking"""
        import logging
        _logger = logging.getLogger(__name__)

        _logger.info("="*80)
        _logger.info(f"DEBUG STOCK PICKING: {self.name}")
        _logger.info(f"Estado: {self.state}")
        _logger.info(f"Número de move_ids: {len(self.move_ids)}")
        _logger.info(f"Número de move_line_ids: {len(self.move_line_ids)}")

        _logger.info("\n--- MOVE_IDS ---")
        for move in self.move_ids:
            _logger.info(f"  Move: {move.product_id.name} - Qty: {move.product_uom_qty} - Location: {move.location_id.complete_name}")

        _logger.info("\n--- MOVE_LINE_IDS ---")
        for move_line in self.move_line_ids:
            _logger.info(f"  MoveLine: {move_line.product_id.name}")
            _logger.info(f"    - quantity: {move_line.quantity}")
            _logger.info(f"    - location_id: {move_line.location_id.complete_name if move_line.location_id else 'None'}")
            _logger.info(f"    - quant_id: {move_line.quant_id.id if move_line.quant_id else 'None'}")
            if move_line.quant_id:
                _logger.info(f"    - quant_id.location_id: {move_line.quant_id.location_id.complete_name}")

        _logger.info("\n--- UBICACIONES CALCULADAS ---")
        _logger.info(f"stock_used_locations: {[loc.complete_name for loc in self.stock_used_locations]}")

        _logger.info("\n--- CATEGORÍAS CALCULADAS ---")
        _logger.info(f"stock_used_categories: {[cat.name for cat in self.stock_used_categories]}")
        _logger.info("="*80)

        return True

    def get_moves_by_location_and_category(self):
        """
        Retorna un diccionario con los movimientos agrupados por ubicación y categoría
        Estructura: {location: {category: [moves]}}
        """
        result = {}

        if self.state == 'done':
            # Para albaranes confirmados, agrupamos por move_line_ids
            for move_line in self.move_line_ids:
                location = move_line.location_id
                category = move_line.product_id.categ_id

                if location not in result:
                    result[location] = {}
                if category not in result[location]:
                    result[location][category] = []

                # Agregamos la move_line al resultado
                if move_line not in result[location][category]:
                    result[location][category].append(move_line)
        else:
            # Para albaranes en borrador/asignados, agrupamos por move_ids
            for move in self.move_ids.filtered(lambda m: m.product_uom_qty > 0):
                location = move.location_id
                category = move.product_id.categ_id

                if location not in result:
                    result[location] = {}
                if category not in result[location]:
                    result[location][category] = []

                result[location][category].append(move)

        return result

    def get_product_availability_info(self, product, quantity_needed, exclude_location=None):
        """
        Verifica la disponibilidad de un producto en otras ubicaciones
        Retorna: dict con información de disponibilidad por ubicación
        """
        StockQuant = self.env['stock.quant']

        # Obtener todas las ubicaciones internas del almacén
        warehouse = self.picking_type_id.warehouse_id
        if not warehouse:
            return {}

        # Buscar stock disponible en ubicaciones internas
        domain = [
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
        ]

        if warehouse:
            domain.append(('location_id.warehouse_id', '=', warehouse.id))

        if exclude_location:
            domain.append(('location_id', '!=', exclude_location.id))

        quants = StockQuant.search(domain)

        availability = {}
        for quant in quants:
            if quant.location_id not in availability:
                availability[quant.location_id] = {
                    'available_qty': 0,
                    'reserved_qty': 0,
                }
            availability[quant.location_id]['available_qty'] += quant.quantity
            availability[quant.location_id]['reserved_qty'] += quant.reserved_quantity

        return availability


class StockMove(models.Model):
    _inherit = "stock.move"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        related="product_id.categ_id",
        string="Categoría",
        store=True,
    )

    def get_availability_in_other_locations(self):
        """Obtiene disponibilidad del producto en otras ubicaciones"""
        self.ensure_one()
        return self.picking_id.get_product_availability_info(
            self.product_id,
            self.product_uom_qty,
            exclude_location=self.location_id
        )


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        related="product_id.categ_id",
        string="Categoría",
        store=True,
    )

    def get_availability_in_other_locations(self):
        """Obtiene disponibilidad del producto en otras ubicaciones"""
        self.ensure_one()
        return self.picking_id.get_product_availability_info(
            self.product_id,
            self.quantity,
            exclude_location=self.location_id
        )

