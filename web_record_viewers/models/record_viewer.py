from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import SQL
from odoo.tools import ormcache

VIEWER_TIMEOUT_SECONDS = 45
GC_OLDER_THAN_SECONDS = VIEWER_TIMEOUT_SECONDS * 2

class RecordViewer(models.Model):
    """
    Tracks users actively viewing specific records across all models.

    Each entry represents one user viewing a particular record.
    Used to provide real-time viewer awareness in form views via bus notifications.

    Access to this model is restricted via ACLs; regular users do not have direct access.
    All interaction should go through HTTP controller endpoints, which use `sudo()` for controlled access.
    """
    _name = 'record.viewer'
    _description = 'Active Record Viewer'
    _log_access = False  # Do not track create/write timestamps per standard Odoo rules

    user_id = fields.Many2one('res.users', required=True, index=True, ondelete='cascade')
    res_model_id = fields.Many2one('ir.model', required=True, index=True, ondelete='cascade')
    res_id = fields.Many2oneReference(required=True, index=True, model_field='res_model')
    write_date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)

    # Convenience fields for frontend display
    user_name = fields.Char(related='user_id.name')
    res_model = fields.Char(related='res_model_id.model')

    _sql_constraints = [
        # Ensure each user has at most one active session per record
        ('user_model_record_uniq', 'unique(user_id, res_model_id, res_id)',
         'A user can only be marked as viewing a record once.')
    ]

    @api.model
    def _get_viewers(self, res_model_id: int, res_id: int):
        """
        Fetches all currently active viewers for the given model ID and record ID.

        This method is typically used by the HTTP controller.
        It uses `sudo()` at the caller level to bypass ACLs on the model itself,
        but assumes the caller has already validated access to the target record.
        """
        timeout_threshold = datetime.now() - timedelta(seconds=VIEWER_TIMEOUT_SECONDS)

        viewers_data = self.search_read(
            [
                ('res_model_id', '=', res_model_id),
                ('res_id', '=', res_id),
                ('write_date', '>', timeout_threshold)
            ],
            ['user_id', 'user_name']
        )
        return [{'id': v['user_id'][0], 'name': v['user_name']} for v in viewers_data]

    @ormcache('ir_model_id')
    @api.model
    def _get_model_name_by_id(self, ir_model_id):
        """
        Retrieves the technical model name (e.g., 'res.partner') for a given ir.model ID.
        Uses Odoo's ORM cache for performance, as model names are static during runtime.
        """
        res = self.env['ir.model'].search_read([('id', '=', ir_model_id)], ['model'], limit=1)
        return res[0]['model'] if res else None

    @api.model
    def _notify_viewers_changed(self, res_model_id: int, res_id: int):
        """
        Sends a bus notification to all users actively viewing a given record.
        The payload includes the updated list of viewers.

        This ensures the frontend stays in sync across all browser clients.
        """
        timeout_threshold = datetime.now() - timedelta(seconds=VIEWER_TIMEOUT_SECONDS)

        active_viewer_records = self.search(
            [
                ('res_model_id', '=', res_model_id),
                ('res_id', '=', res_id),
                ('write_date', '>', timeout_threshold)
            ]
        )

        message_payload = {
            'res_model': (
                active_viewer_records[0].res_model
                if active_viewer_records else self._get_model_name_by_id(res_model_id)
            ),
            'res_id': res_id,
            'viewers': [{'id': v.user_id.id, 'name': v.user_name} for v in active_viewer_records],
        }

        active_viewer_records.user_id._bus_send('record_viewers_update', message_payload)

    @api.model
    def _start_session(self, res_model_id: int, res_id: int):
        """
        Creates or refreshes a viewer session for the current user on a given record.

        Uses raw SQL with UPSERT to ensure the viewer entry is created or updated atomically.
        `sudo()` is typically used by the controller to bypass direct model ACLs.
        Assumes caller has already performed permission checks on the target record.
        """
        user_id = self.env.uid
        self.env.cr.execute(SQL("""
            INSERT INTO %s (user_id, res_model_id, res_id, write_date)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, res_model_id, res_id)
            DO UPDATE SET write_date = EXCLUDED.write_date
        """, SQL.identifier(self._table), user_id, res_model_id, res_id, fields.Datetime.now()))

        self._notify_viewers_changed(res_model_id, res_id)

    @api.model
    def _stop_session(self, res_model_id: int, res_id: int):
        """
        Ends the viewer session for the current user on the given record.
        If a record was deleted, triggers a notification to update other clients.
        """
        user_id = self.env.uid
        self.env.cr.execute(SQL("""
            DELETE FROM %s
            WHERE res_model_id = %s AND res_id = %s AND user_id = %s
        """, SQL.identifier(self._table), res_model_id, res_id, user_id))

        if self.env.cr.rowcount:
            self._notify_viewers_changed(res_model_id, res_id)

    def _cron_cleanup_stale_viewers(self):
        """
        Automatically removes stale viewer sessions whose `write_date`
        has expired beyond the timeout threshold.

        This runs via Odoo's autovacuum mechanism and keeps the viewer
        table clean and performant. Bus notifications are sent to reflect
        any changes to active viewers.
        """
        self.env.cr.execute(SQL("""
            DELETE FROM %s
            WHERE write_date < (NOW() AT TIME ZONE 'UTC' - INTERVAL '%s seconds')
            RETURNING id, res_model_id, res_id
        """, SQL.identifier(self._table), GC_OLDER_THAN_SECONDS))

        deleted_records = self.env.cr.fetchall()
        if not deleted_records:
            return

        # Deduplicate (res_model_id, res_id) pairs for notification
        stale_viewers_to_notify = {
            (res_model_id, res_id)
            for _, res_model_id, res_id in deleted_records
        }

        for res_model_id, res_id in stale_viewers_to_notify:
            self._notify_viewers_changed(res_model_id, res_id)
