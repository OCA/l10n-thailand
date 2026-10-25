## 20.0.1.0.0

- Renamed from `l10n_th_tax_address`.
- No dependency on `l10n_th_partner` and `l10n_th_base_location`
  anymore: the Branch Code is the standard `TH_BRANCH_CODE` partner
  identifier and the provinces are the standard Thai states.
- The RD data is written through a configurable field mapping; by
  default the fields are filled as in version 16.
- A new contact is filled as soon as its Tax ID is typed, and the
  Branch Code is set from the RD answer.
