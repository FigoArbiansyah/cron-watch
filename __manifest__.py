# -*- coding: utf-8 -*-
{
    'name': 'CronWatch',
    'version': '17.0.1.0.0',
    'summary': 'Track and monitor scheduled actions (cron jobs) execution with detailed logs',
    'description': """
Scheduled Actions Tracker
==========================
A comprehensive monitoring module for Odoo scheduled actions (cron jobs).

Features:
- Job-Level Tracking: Activate logging only for the cron jobs that need monitoring.
- Execution Visibility: View trigger type, status, triggering source and duration.
- Execution History: Keep a clear record of job runs and outcomes over time.
- In-App Error Review: Check execution errors directly in Odoo without going to server logs.
    """,
    'author': 'Custom Module',
    'category': 'Technical',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_actions_tracker_data.xml',
        'views/cron_log_views.xml',
        'views/ir_cron_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'scheduled_actions_tracker/static/src/css/tracker.css',
            'scheduled_actions_tracker/static/src/js/dashboard.js',
            'scheduled_actions_tracker/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
