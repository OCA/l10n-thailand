Administrators can configure the default year display from **Settings >
General Settings**:

Inside the **Regional Formats** block beside the **Languages** section:

- **Date Year Format** controls whether users see Common Era (CE) or Buddhist
  Era (BE) years by default.
- **Auto-correct BE Manual Input** controls how manually typed BE years are
  detected and converted back to CE before normal Odoo parsing.

``Date Year Format`` sets the system default:

- ``Common Era (CE)``
- ``Buddhist Era (BE)``

``Auto-correct BE Manual Input`` controls how manually typed 4-digit years are
recognized and converted back to CE before save:

- ``Half of 543 years ahead``
- ``100 years ahead``
- ``200 years ahead``

Each user can override the system year display from their user preferences.
