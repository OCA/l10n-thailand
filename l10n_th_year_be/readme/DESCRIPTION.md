This module lets users display date, datetime, and date range widgets with
Buddhist Era (BE) years while Odoo continues to store all values as Common Era
(CE) dates and datetimes.

The conversion is display-only. For example, a stored date in 2026 can be
shown as 2569, but the database value remains 2026. ORM values, database
values, RPC payloads, timezone handling, and date arithmetic remain CE.

The module now supports a four-layer year-format architecture. The effective
format is resolved from the most specific layer to the most general layer:

1. XML element-level option
2. Python field-level option
3. User preference
4. System setting

Supported ``year_format`` values are:

- ``system``
- ``ce``
- ``be``

The module also provides client-side correction of manually typed BE years
back to CE before Odoo parses and stores the value.

Backend features include:

- system-wide year-format settings on ``res.config.settings``;
- per-user year-format preference on ``res.users``;
- ``fields.Date`` and ``fields.Datetime`` metadata exposure for
  ``year_format``;
- QWeb ``date`` and ``datetime`` rendering support.

Frontend features include:

- form-view ``date``, ``datetime``, and ``daterange`` widgets;
- list-view ``date``, ``datetime``, and ``daterange`` widgets;
- date picker and datetime picker year labels;
- editable input normalization before parsing.
