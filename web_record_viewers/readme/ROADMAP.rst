The following enhancements are planned for future versions of the ``web_record_viewers`` module. These aim to expand its versatility, configurability, and user experience while remaining lightweight and unobtrusive.

Support for Other View Types
----------------------------

* Extend viewer tracking support beyond form views to include:
  
  - Kanban views
  - List (tree) views
  - Possibly activity or calendar views

* Display viewer indicators contextually in these views, possibly via badges, tooltips, or side panels.

Improved UI/UX
--------------

* Add a tooltip to each viewer badge that displays the full name and, if available, the user's avatar.
* Improve accessibility and responsiveness of the viewer strip.

Opt-Out Mechanism
------------------

* Allow users to opt out of viewer visibility (e.g., "Invisible Mode") through a user preference.
* Option to anonymize viewer display or replace names with generic placeholders if privacy settings are enabled.

Configuration for Timeout and Refresh Interval
-----------------------------------------------

* Introduce module-level configuration settings (via `ir.config_parameter` or a Settings model) to control:

  - Viewer session timeout duration (default: 45 seconds)
  - Frontend ping interval (default: 30 seconds)

* Make these values adjustable without requiring source code changes or redeployments.