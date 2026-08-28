# -*- coding: utf-8 -*-
"""Relanza el backfill de 'Responsable de venta' en cada actualización.

El `post_init_hook` solo corre al instalar el módulo; los saltos de versión
(OpenUpgrade) y las cargas masivas dejan `sale_responsible_id` vacío en
asientos/apuntes cuyo partner sí tiene responsable. Este script hace que el
recálculo se dispare solo en cada `-u enteza_sales_manager` con versión nueva,
sin depender de que alguien lance la server action a mano.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.enteza_sales_manager.hooks import _recompute_sale_responsible


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _recompute_sale_responsible(env)
