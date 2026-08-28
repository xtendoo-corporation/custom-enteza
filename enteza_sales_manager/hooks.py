# -*- coding: utf-8 -*-


def _recompute_sale_responsible(env):
    """Recalcula 'sale_responsible_id' en facturas/asientos y en sus apuntes.

    El campo es un compute+store (ver models/account_move.py y
    models/account_move_line.py) que depende de 'partner_id.sale_responsible_id'.
    Odoo solo dispara ese recálculo cuando el ORM crea o escribe el registro.

    Los asientos generados por procesos de carga masiva (asientos de
    apertura de una migración OpenUpgrade, importaciones directas, etc.)
    insertan filas sin pasar por create()/write() del ORM en el momento en
    que el partner ya tenía su responsable asignado, así que el campo se
    queda vacío aunque el partner sí tenga un 'Responsable de venta'.

    Esta función se usa tanto en el post_init_hook (instalación en una BD
    nueva) como en la server action manual 'Recalcular responsable de
    venta', para poder relanzar el backfill cada vez que haga falta (por
    ejemplo, después de cada salto de versión en una migración OpenUpgrade).
    """
    moves = env['account.move'].search([('sale_responsible_id', '=', False)])
    if moves:
        moves._compute_sale_responsible()

    lines = env['account.move.line'].search([('sale_responsible_id', '=', False)])
    if lines:
        lines._compute_sale_responsible()


def post_init_hook(env):
    _recompute_sale_responsible(env)
