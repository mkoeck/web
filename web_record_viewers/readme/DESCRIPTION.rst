This module enables real-time awareness of who is currently viewing a specific record in the Odoo backend interface. When users open a form view of any record, a non-intrusive badge strip is shown listing the names of other active viewers. This feature enhances team collaboration by avoiding edit conflicts and promoting transparency.

Features
--------

- ⏱️ **Live Viewer Tracking**:
  Displays which users are actively viewing the same record on form views, updated in real time using Odoo's bus service.

- 🔄 **Automatic Session Refresh**:
  Viewer sessions are kept alive via periodic client-side pings (every 30 seconds), ensuring accurate presence detection.

- 🚦 **Conflict Minimization**:
  Helps prevent accidental data overwrites in multi-user environments by raising visibility of concurrent access.

- 🔐 **Secure Access Control**:
  Viewer data is accessed via controller routes that enforce model-level and record-level read access rules. The underlying `record.viewer` model uses `sudo()` operations internally but only after access validation.

- 🧹 **Stale Session Cleanup**:
  A cron job periodically removes expired viewer records (after ~90 seconds) to keep data lean and relevant.

- ⚙️ **Generic and Reusable**:
  Works across all models in Odoo by dynamically tracking the model and record ID — no special configuration required.

Technical Design
----------------

- The `record.viewer` model stores user, model, and record references along with `write_date` as the activity timestamp.
- Controller endpoints (`GET`, `POST`, `DELETE`) manage session state and are protected by access decorators.
- A frontend patch of `FormController` handles:
  
  - Session lifecycle (start/stop)
  - Viewer polling and bus subscription
  - UI rendering of active viewers

- Frontend assets include:
  
  - `form_controller.js`: session handling and viewer updates
  - `form_controller.xml`: viewer badge UI
  - `form_controller.scss`: styling for viewer display strip

- A cron job defined in `ir_cron.xml` periodically removes stale sessions older than 90 seconds and notifies remaining users accordingly.

Use Cases
---------

- Multi-user environments where real-time awareness of record access can help avoid duplication or miscommunication.
- Shared CRM or Helpdesk records where coordination is key.
- Educational or onboarding use where instructors monitor trainee activity.