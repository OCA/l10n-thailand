Once installed, the module applies to backend date, datetime, and date range
widgets according to the effective year format.

The priority order is:

1. XML element-level option: ``year_format``
2. Python field-level option: ``year_format``
3. User preference: ``Date Year Format``
4. System setting: ``Date Year Format``

Each user can choose ``Date Year Format`` in user preferences:

- ``System Default``
- ``Common Era (CE)``
- ``Buddhist Era (BE)``

Developers can define a field-level default on Python ``fields.Date`` and
``fields.Datetime``:

```python
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    validity_date = fields.Date(year_format="be")
    commitment_date = fields.Datetime(year_format="ce")
    expected_date = fields.Date(year_format="system")
```

Developers can force a specific behavior on a field:

```xml
<field name="date_order" options="{'year_format': 'be'}" />
<field name="commitment_date" options="{'year_format': 'ce'}" />
<field name="expected_date" options="{'year_format': 'system'}" />
```

If omitted, the XML layer falls back to Python field-level configuration, then
user preference, then system setting.

QWeb date and datetime output uses the same ``year_format`` values:

```xml
<span t-field="o.date_order"
      t-options="{'widget': 'date', 'year_format': 'be'}"/>

<span t-field="o.commitment_date"
      t-options="{'widget': 'datetime', 'year_format': 'ce'}"/>

<span t-field="o.validity_date"
      t-options="{'widget': 'date', 'year_format': 'system'}"/>
```

For QWeb, the precedence is still:

1. QWeb element ``year_format``
2. Python field-level ``year_format``
3. User preference
4. System setting

Examples:

```xml
<list string="Sales Orders">
  <field name="name" />
  <field name="date_order" options="{'year_format': 'be'}" />
  <field name="commitment_date" options="{'year_format': 'ce'}" />
  <field name="expected_date" options="{'year_format': 'system'}" />
</list>
```

```xml
<form string="Sales Order">
  <sheet>
    <group>
      <field name="date_order" options="{'year_format': 'be'}" />
      <field name="commitment_date" options="{'year_format': 'system'}" />
      <field name="validity_date" options="{'year_format': 'ce'}" />
    </group>
  </sheet>
</form>
```

```xml
<field
  name="start_date"
  widget="daterange"
  options="{
        'start_date_field': 'start_date',
        'end_date_field': 'end_date',
        'year_format': 'be'
    }"
/>
```

Users can edit dates as usual. When BE manual input correction is enabled and
a typed year matches the selected detection strategy, the client converts only
the year back to CE before saving.

Important manual-input rules:

- only 4-digit years are considered;
- 2-digit years are intentionally not interpreted;
- conversion affects typed input before save/parsing only;
- stored values remain CE.

The typed year is converted to CE only when it is greater than the configured
CE threshold and no later than the current BE year.
