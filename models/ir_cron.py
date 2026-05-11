# -*- coding: utf-8 -*-
import logging
import traceback
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = 'ir.cron'

    # ─── Configuration ─────────────────────────────────────────────────────────
    enable_tracking = fields.Boolean(
        string='Enable Execution Tracking',
        default=False,
        help='When enabled, every execution of this scheduled action will be '
             'recorded in the Execution Log.',
    )
    log_retention_days = fields.Integer(
        string='Log Retention (days)',
        default=30,
        help='Automatically delete logs older than this many days. '
             'Set to 0 to keep logs indefinitely.',
    )

    # ─── Statistics (computed from logs) ──────────────────────────────────────
    log_count = fields.Integer(
        string='Executions',
        compute='_compute_log_stats',
    )
    last_execution = fields.Datetime(
        string='Last Execution',
        compute='_compute_log_stats',
    )
    last_status = fields.Selection(
        selection=[
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        string='Last Status',
        compute='_compute_log_stats',
    )
    success_count = fields.Integer(
        string='Successes',
        compute='_compute_log_stats',
    )
    failure_count = fields.Integer(
        string='Failures',
        compute='_compute_log_stats',
    )
    avg_duration = fields.Float(
        string='Avg Duration (s)',
        compute='_compute_log_stats',
        digits=(10, 3),
    )

    # ──────────────────────────────────────────────────────────────────────────
    # Compute
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_log_stats(self):
        CronLog = self.env['cron.log']
        for cron in self:
            logs = CronLog.search([('cron_id', '=', cron.id)])
            cron.log_count = len(logs)
            if logs:
                latest = logs.sorted('start_datetime', reverse=True)[0]
                cron.last_execution = latest.start_datetime
                cron.last_status = latest.state
                cron.success_count = len(logs.filtered(lambda l: l.state == 'success'))
                cron.failure_count = len(logs.filtered(lambda l: l.state == 'failed'))
                done = logs.filtered(lambda l: l.duration > 0)
                cron.avg_duration = sum(done.mapped('duration')) / len(done) if done else 0.0
            else:
                cron.last_execution = False
                cron.last_status = False
                cron.success_count = 0
                cron.failure_count = 0
                cron.avg_duration = 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # Override: intercept cron execution
    # ──────────────────────────────────────────────────────────────────────────

    def _callback(self, cron_name, server_action_id, job_id):
        """Override to wrap execution with tracking."""
        cron = self.browse(job_id)
        if not cron.enable_tracking:
            return super()._callback(cron_name, server_action_id, job_id)

        CronLog = self.env['cron.log'].sudo()
        log = CronLog.create({
            'cron_id': job_id,
            'trigger_type': 'scheduled',
            'start_datetime': fields.Datetime.now(),
            'state': 'running',
        })
        # commit so the "Running" entry is visible immediately
        self.env.cr.commit()

        try:
            super()._callback(cron_name, server_action_id, job_id)
            log.sudo().write({
                'end_datetime': fields.Datetime.now(),
                'state': 'success',
            })
        except Exception as exc:
            tb = traceback.format_exc()
            _logger.exception(
                'Scheduled action %s failed (tracked)', cron_name
            )
            log.sudo().write({
                'end_datetime': fields.Datetime.now(),
                'state': 'failed',
                'error_message': str(exc),
                'error_traceback': tb,
            })
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Manual Trigger
    # ──────────────────────────────────────────────────────────────────────────

    def method_direct_trigger(self):
        """Override to log manual triggers."""
        for cron in self:
            if not cron.enable_tracking:
                return super().method_direct_trigger()

            CronLog = self.env['cron.log'].sudo()
            log = CronLog.create({
                'cron_id': cron.id,
                'trigger_type': 'manual',
                'triggered_by': self.env.uid,
                'start_datetime': fields.Datetime.now(),
                'state': 'running',
            })
            self.env.cr.commit()

            try:
                result = super(IrCron, cron).method_direct_trigger()
                log.sudo().write({
                    'end_datetime': fields.Datetime.now(),
                    'state': 'success',
                })
                return result
            except Exception as exc:
                tb = traceback.format_exc()
                log.sudo().write({
                    'end_datetime': fields.Datetime.now(),
                    'state': 'failed',
                    'error_message': str(exc),
                    'error_traceback': tb,
                })
                raise

    # ──────────────────────────────────────────────────────────────────────────
    # Smart Buttons / Actions
    # ──────────────────────────────────────────────────────────────────────────

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Execution Logs — %s') % self.name,
            'res_model': 'cron.log',
            'view_mode': 'tree,form',
            'domain': [('cron_id', '=', self.id)],
            'context': {'default_cron_id': self.id},
        }

    def action_purge_old_logs(self):
        """Manually purge logs beyond retention period."""
        self.ensure_one()
        if not self.log_retention_days:
            raise UserError(_('Log retention is set to unlimited for this action.'))
        cutoff = fields.Datetime.subtract(
            fields.Datetime.now(), days=self.log_retention_days
        )
        old_logs = self.env['cron.log'].search([
            ('cron_id', '=', self.id),
            ('start_datetime', '<', cutoff),
        ])
        count = len(old_logs)
        old_logs.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Logs Purged'),
                'message': _('%d log(s) older than %d days have been deleted.') % (
                    count, self.log_retention_days
                ),
                'type': 'success',
                'sticky': False,
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Scheduled cleanup cron (called by the data cron)
    # ──────────────────────────────────────────────────────────────────────────

    @api.model
    def _gc_cron_logs(self):
        """Garbage-collect old logs for all tracked crons that have a retention set."""
        tracked = self.search([
            ('enable_tracking', '=', True),
            ('log_retention_days', '>', 0),
        ])
        for cron in tracked:
            cutoff = fields.Datetime.subtract(
                fields.Datetime.now(), days=cron.log_retention_days
            )
            self.env['cron.log'].search([
                ('cron_id', '=', cron.id),
                ('start_datetime', '<', cutoff),
            ]).unlink()
        _logger.info('cron.log GC: processed %d tracked crons.', len(tracked))
