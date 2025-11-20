# -*- coding: utf-8 -*-
{
    'name': 'Enteza Imports',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Importación de clientes desde Excel',
    'description': """
        Módulo para importar clientes desde archivos Excel.
        Permite importar información de contactos incluyendo direcciones de envío y facturación.
    """,
    'author': 'Enteza',
    'website': 'https://www.enteza.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizards/import_customers_wizard_views.xml',
        'wizards/import_products_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
