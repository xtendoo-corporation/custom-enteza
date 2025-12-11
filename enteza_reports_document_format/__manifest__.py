# -*- coding: utf-8 -*-

{
    "name": "Enteza Reports Document Format",
    "summary": """Formatos de documentos personalizados para Enteza""",
    "version": "19.0.1.0.0",
    "description": """
        Formatos de documentos personalizados para reportes de:
        - Pedidos de venta
        - Albaranes
        - Facturas
        Agrupados por categorías de producto
    """,
    "author": "Dani Domínguez, Manuel Calero, Abraham Carrasco - Xtendoo",
    "company": "Xtendoo",
    "website": "https://www.xtendoo.es",
    "category": "Reporting",
    "depends": [
        "base",
        "sale",
        "stock",
        "sale_management",
        "account",
    ],
    "license": "AGPL-3",
    "data": [
        # Ventas
        "views/sale/sale_order_views.xml",
        "views/sale/report_saleorder_document.xml",
        # Stock
        "views/stock/stock_picking_views.xml",
        "views/stock/report_stockpicking_document.xml",
        # Contabilidad
        "views/account/account_move_views.xml",
        "views/account/report_accountmove_document.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}

