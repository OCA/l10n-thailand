## 20.0.1.0.0

**Breaking changes**

- Rebuilt on top of the standard `l10n_th` and
  `l10n_account_withholding_tax` modules. The withholding taxes are
  standard taxes (`Is Withholding Tax`). Tax invoices and withholding
  tax certificates apply to Thai companies only.
- Removed the models `account.withholding.tax` and
  `account.withholding.move`, the `WHT Account` flag on accounts, the
  withholding tax on products and `wht_tax_id` on journal items.
- The standard Thai tax invoices of `l10n_th` (`VAT Registered`) are
  not created, the tax invoices of this module are used instead.
- Removed the `Default Type of Income` of taxes, the type of income of
  the certificates defaults from the standard `Income Tax Type`.
- There is no data migration from older versions.
