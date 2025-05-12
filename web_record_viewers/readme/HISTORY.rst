18.0.1.0.0 (2025-05-12)
=======================

- Initial release of ``web_record_viewers``.
- Tracks which users are actively viewing a given record (form views only).
- Viewer data is updated in real time using Odoo's bus service.
- Adds frontend UI with badge strip showing concurrent viewers.
- Includes server-side cron job for cleaning up stale sessions.
- All access to viewer data is gated through HTTP controllers with enforced model-level and record-level security checks.
- Fully integrated with the Odoo web client using OWL and patching the FormController.
- Adds unittests for core model methods and bus event triggers.