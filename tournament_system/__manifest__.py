{
    'name': 'Tournament System',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'Tournament System',
    'description': 'This module allows you to manage tournaments and matches for a sports event.',
    'author': 'leonardo02lobo',
    'icon': '/static/description/torneos de LOL.png',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/tournament_views.xml',
        'views/event_tournament_views.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True
}