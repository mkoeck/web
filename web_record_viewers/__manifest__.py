# -*- coding: utf-8 -*-
{
    'name': "Web Record Viewers",

    'summary': "Shows which other users are currently viewing a record",
    'version': "18.0.1.0.0",
    'development_status': 'Alpha',
    'category': 'Usability',
    'website': 'https://github.com/OCA/web',
    'author': 'Michael Köck, Odoo Community Association (OCA)',
    "maintainers": ["mkoeck"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    'depends': ['bus', 'web'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'web_record_viewers/static/src/views/form/form_controller.js',
            'web_record_viewers/static/src/views/form/form_controller.xml',
            'web_record_viewers/static/src/views/form/form_controller.scss',
        ],
    },
}

