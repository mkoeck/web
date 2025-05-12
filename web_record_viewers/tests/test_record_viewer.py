from odoo.tests import TransactionCase
from time import sleep
from unittest.mock import patch

class RecordViewerTests(TransactionCase):
    def test_get_model_name_by_id(self):
        ir_model = self.env['ir.model'].search([], limit=1)
        name = self.env['record.viewer']._get_model_name_by_id(ir_model.id)
        self.assertEqual(ir_model.model, name, 'Name lookup failed')

    def test_start_session(self):
        self.env['record.viewer']._start_session(1, 1)
        
        self.env.cr.execute("SELECT write_date FROM record_viewer")
        write_date = self.env.cr.dictfetchall()

        self.assertEqual(len(write_date), 1, "There should be one record.viewer entry after calling _start_session once")

        sleep(1) # 1 second delay, to ensure write date is actually updated

        self.env['record.viewer']._start_session(1, 1)
        self.env.cr.execute("SELECT write_date FROM record_viewer")
        updated_write_date = self.env.cr.dictfetchall()

        self.assertEqual(len(write_date), 1, "There should be one record.viewer entry after calling _start_session twice on the same record")
        self.assertGreater(updated_write_date[0]["write_date"], write_date[0]["write_date"], "The write date should be updated after calling _start_session twice on the same record")

        self.env['record.viewer']._start_session(1, 2)
        self.env.cr.execute("SELECT write_date FROM record_viewer")
        recs = self.env.cr.dictfetchall()
        self.assertEqual(len(recs), 2, "After calling _start session on two different records, there should be to record.viewer records")

        self.env['record.viewer'].sudo().with_user(2)._start_session(1, 2)
        self.env.cr.execute("SELECT DISTINCT user_id FROM record_viewer")
        recs = self.env.cr.dictfetchall()
        self.assertEqual(len(recs), 2, "Calling _start_session with two different users should create a new record.viewer")

    def test_notify_viewers_changed(self):
        with patch('odoo.addons.bus.models.bus_listener_mixin.BusListenerMixin._bus_send', autospec=True) as mock_bus_send:
            # Start session creates initial viewer --> notify one user that one user is viewing
            self.env['record.viewer']._start_session(1, 1)
            self.assertEqual(mock_bus_send.call_count, 1, "Calling _start_session should send a message to the bus")
            args, _ = mock_bus_send.call_args
            self.assertEqual(args[1], 'record_viewers_update', "Calling _start_session should send a 'record_viewers_update' message to the bus")
            self.assertEqual(len(args[0]), 1, 'One user should be notified after calling start_session once')
            model_name = self.env['record.viewer']._get_model_name_by_id(1)
            expected_payload = {
                'res_model': model_name,
                'res_id': 1,
                'viewers': [{
                    'id': self.env.user.id,
                    'name': self.env.user.name
                }]
            }
            self.assertDictEqual(expected_payload, args[2])

            # Stop session should delete previously created record --> notify no remaining users that no one is viewing
            self.env['record.viewer']._stop_session(1, 1)
            self.assertEqual(mock_bus_send.call_count, 2, "Calling _stop_session should send a message to the bus")
            args, _ = mock_bus_send.call_args
            expected_payload = {
                'res_model': model_name,
                'res_id': 1,
                'viewers': []
            }
            self.assertEqual(len(args[0]), 0, 'No user should be notified if calling _stop_session after start_session on the same record')
            self.assertDictEqual(expected_payload, args[2])

            # Start session twice with two different users --> notify two users
            self.env['record.viewer']._start_session(1, 1)
            self.env['record.viewer'].with_user(2)._start_session(1, 1)
            args, _ = mock_bus_send.call_args
            self.assertEqual(len(args[0]), 2, 'Two users should be notified if calling _start_session twice on the same record with different users')

    def test_get_viewers(self):
        self.env['record.viewer']._start_session(1, 1)
        payload = self.env['record.viewer']._get_viewers(1, 1)
        expected_payload = [
            {
                'id': self.env.user.id,
                'name': self.env.user.name
            }
        ]

        self.assertListEqual(payload, expected_payload)