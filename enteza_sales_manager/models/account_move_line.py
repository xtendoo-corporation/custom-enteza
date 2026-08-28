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

    @api.depends(
        'partner_id', 'partner_id.sale_responsible_id',
        'move_id', 'move_id.sale_responsible_id',
    )
    def _compute_sale_responsible(self):
        for line in self:
            # Priorizar el responsable del partner de la línea si existe,
            # en caso contrario usar el responsable de la factura/asiento (move_id)
            if line.partner_id and line.partner_id.sale_responsible_id:
                line.sale_responsible_id = line.partner_id.sale_responsible_id
            elif line.move_id and getattr(line.move_id, 'sale_responsible_id', False):
                line.sale_responsible_id = line.move_id.sale_responsible_id
            else:
                line.sale_responsible_id = False

    def _inverse_sale_responsible(self):
        for line in self:
            # Si la línea tiene partner, propagar al partner. Si no, intentar propagar al move
            if line.partner_id:
                try:
                    line.partner_id.sale_responsible_id = line.sale_responsible_id
                except Exception:
                    pass
            elif line.move_id:
                try:
                    line.move_id.sale_responsible_id = line.sale_responsible_id
                except Exception:
                    pass

    def action_recompute_sale_responsible(self):
        """Recalcula 'Responsable de venta' bajo demanda.

        Pensado para apuntes que nunca dispararon el compute porque se
        crearon fuera del ORM (asientos de apertura de una migración
        OpenUpgrade, importaciones directas, etc.) y por tanto se quedaron
        con el campo vacío aunque el partner ya tuviera un responsable
        asignado.

        - Si se lanza con una selección de apuntes (desde el menú de
          acciones de la lista), recalcula solo esos.
        - Si se lanza sin selección, recalcula todos los apuntes (y sus
          asientos) que todavía tengan el campo vacío.
        """
        lines = self if self else self.search([('sale_responsible_id', '=', False)])
        lines._compute_sale_responsible()
        lines.move_id._compute_sale_responsible()
        return True




