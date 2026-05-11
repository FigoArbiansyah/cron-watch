# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CronLog(models.Model):
    _name = 'cron.log'
    _description = 'Scheduled Action Execution Log'
    _order = 'start_datetime desc'
    _rec_name = 'cron_id'

    # ─── Relational ───────────────────────────────────────────────────────────
    cron_id = fields.Many2one(
        'ir.cron',
        string='Scheduled Action',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ─── Execution Info ────────────────────────────────────────────────────────
    trigger_type = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('manual', 'Manual'),
        ],
        string='Trigger Type',
        required=True,
        default='scheduled',
    )
    triggered_by = fields.Many2one(
        'res.users',
        string='Triggered By',
        help='The user who manually triggered this action (if applicable).',
    )
    start_datetime = fields.Datetime(
        string='Start Time',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    end_datetime = fields.Datetime(
        string='End Time',
    )
    duration = fields.Float(
        string='Duration (s)',
        compute='_compute_duration',
        store=True,
        digits=(10, 3),
        help='Execution duration in seconds.',
    )
    duration_human = fields.Char(
        string='Duration',
        compute='_compute_duration',
        store=True,
    )

    # ─── Status ────────────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        string='Status',
        required=True,
        default='running',
        index=True,
    )

    # ─── Error Details ─────────────────────────────────────────────────────────
    error_message = fields.Text(
        string='Error Message',
        help='Short error summary.',
    )
    error_traceback = fields.Text(
        string='Traceback',
        help='Full Python traceback when execution failed.',
    )

    # ─── Related info (denormalised for speed) ─────────────────────────────────
    cron_model = fields.Char(
        string='Model',
        related='cron_id.model_id.model',
        store=True,
    )
    cron_method = fields.Text(
        string='Method',
        related='cron_id.code',
        store=True,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # Compute
    # ──────────────────────────────────────────────────────────────────────────

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                secs = delta.total_seconds()
                rec.duration = secs
                rec.duration_human = rec._format_duration(secs)
            else:
                rec.duration = 0.0
                rec.duration_human = '—'

    @staticmethod
    def _format_duration(secs):
        if secs < 1:
            return f'{secs * 1000:.0f} ms'
        if secs < 60:
            return f'{secs:.2f} s'
        mins = int(secs // 60)
        remaining = secs % 60
        return f'{mins}m {remaining:.0f}s'

    # ──────────────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────────────

    def action_view_error(self):
        """Open a dialog showing the full traceback."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Error Details',
            'res_model': 'cron.log',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'scheduled_actions_tracker.cron_log_error_form_view'
            ).id,
            'target': 'new',
        }

    @api.model
    def get_dashboard_stats(self):
        """Fetch statistics for the dashboard."""
        today = fields.Date.today()
        start_of_day = fields.Datetime.to_string(
            fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )

        # 1. Summary Widgets
        runs_today = self.search_count([('start_datetime', '>=', start_of_day)])
        success_today = self.search_count([
            ('start_datetime', '>=', start_of_day),
            ('state', '=', 'success')
        ])
        success_rate = (success_today / runs_today * 100) if runs_today > 0 else 0

        slowest_job = self.search([
            ('start_datetime', '>=', start_of_day),
            ('state', '!=', 'running')
        ], order='duration desc', limit=1)

        # 2. Execution Trend (Last 7 Days)
        trend_data = []
        for i in range(6, -1, -1):
            date = today - relativedelta(days=i)
            date_str = fields.Date.to_string(date)
            
            success_count = self.search_count([
                ('start_datetime', '>=', date_str + ' 00:00:00'),
                ('start_datetime', '<=', date_str + ' 23:59:59'),
                ('state', '=', 'success')
            ])
            failed_count = self.search_count([
                ('start_datetime', '>=', date_str + ' 00:00:00'),
                ('start_datetime', '<=', date_str + ' 23:59:59'),
                ('state', '=', 'failed')
            ])
            
            trend_data.append({
                'date': date.strftime('%a, %d %b'),
                'success': success_count,
                'failed': failed_count,
            })

        # 3. Failure Heatmap (Last 30 Days, grouped by hour)
        heatmap_data = []
        last_30_days = today - relativedelta(days=30)
        failures = self.search([
            ('start_datetime', '>=', fields.Date.to_string(last_30_days)),
            ('state', '=', 'failed')
        ])
        
        hour_counts = [0] * 24
        for fail in failures:
            # We use UTC hour or local? Odoo fields are UTC. 
            # For heatmap, local hour is usually better if the user is in a specific timezone.
            # But let's stick to UTC for now or use user's TZ if possible.
            hour = fail.start_datetime.hour 
            hour_counts[hour] += 1
            
        for h in range(24):
            heatmap_data.append({
                'hour': f"{h:02d}:00",
                'count': hour_counts[h]
            })

        return {
            'summary': {
                'total_runs': runs_today,
                'success_rate': round(success_rate, 1),
                'slowest_job_name': slowest_job.cron_id.name if slowest_job else 'None',
                'slowest_job_duration': slowest_job.duration_human if slowest_job else '0s',
            },
            'trend': trend_data,
            'heatmap': heatmap_data,
        }
