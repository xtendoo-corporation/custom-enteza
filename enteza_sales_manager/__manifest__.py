{
    'name': 'Enteza Sales Manager',
    'version': '1.0.0',
    'summary': 'Añade Responsable de venta en contactos y facturas',
    'category': 'Sales',
    'author': 'enteza',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'sale', 'sale_renting'],
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_search_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}

