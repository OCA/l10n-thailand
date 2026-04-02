## Bank Template Section

Defines how the template lines are grouped and iterated during file
generation. Sections support a **parent/child hierarchy** to build
complex file structures (e.g. Header -> Detail -> Footer).

Menu: *Settings \> Technical \> Bank Template \> Bank Section*

Section Fields:

- **Name**: Label for the section.
- **Sequence**: Controls the rendering order.
- **Parent Section**: Link to a parent section (for nesting).
- **Data Level**: Determines what data the section iterates over:
  - `Document` - Rendered once using the export document.
  - `Payment` - Rendered once per active payment line.
  - `Invoice` - Rendered once per invoice on each payment.
  - `Withholding Tax` - Rendered once per WHT certificate on each
    payment.
  - `Custom Expression` - Uses a custom Python iterable.

## Bank Template

Defines the structure of the output **text file** according to the
bank's specifications. Each template contains an ordered list of
template lines.

Menu: *Settings \> Technical \> Bank Template \> Bank Template*

Template Fields:

- **Name**: Template name.
- **Bank**: Bank selection (extended by bank-specific modules).
- **Line Ending**: End-of-line character (`\r\n`, `\n`, or none).

Template Line Fields:

- **Description**: Explanation of the field.
- **Field Length**: Maximum character length of the output value.
- **From / To**: Auto-computed character position range based on
  sequence and field lengths. Resets at each section separator.
- **Condition**: Python expression; if it evaluates to `False`, the
  line is skipped.
- **Section**: Links the line to a `Bank Template Section` for
  grouping and iteration control.
- **Alignment**: Align value to **Left** or **Right** within the
  field length.
- **Padding**: Filler character if the value is shorter than the
  defined length (default: space).
- **Source Type**: `Fixed Value` for static text, `Python Expression`
  for dynamic value.
- **Fixed Value**: Static text (only when Source Type = Fixed).
- **Expression**: Python expression evaluated at runtime (only when
  Source Type = Expression).

### Python Expression Variables

**Global Variables** (always available):

- `rec`: The export document (`bank.payment.export`)
- `lines`: All active export lines (`bank.payment.export.line`)
- `today`: Current date
- `today_datetime`: Current date and time

**Context Variables** (depend on the Section's **Data Level**):

- **Document Level**: Only global variables are available.
- **Payment Level**:
  - `line`: Current export line (`bank.payment.export.line`)
  - `idx_payment`: Index of the current payment
  - `payment`: Current payment (`account.payment`)
  - `invoices`: All reconciled invoices for the payment
  - `wht_certs`: All WHT certificates for the payment
- **Invoice Level** (includes Payment variables):
  - `invoice`: Current invoice (`account.move`)
  - `idx_invoice`: Index of the current invoice
- **Withholding Tax Level** (includes Payment variables):
  - `wht_cert`: Current WHT certificate (`withholding.tax.cert`)
  - `idx_wht`: Index of the current WHT certificate
- **Custom Expression Level**:
  - `payment_line`: Current export line
  - `payment`: Current payment
  - `sub_line`: Current iterated object from the custom expression
  - `idx_sub_line`: Index of the current sub-loop item

## Bank Payment Profile

Used to **pre-configure default values** for the Bank Payment Export
form, reducing manual data entry and errors.

Menu: *Invoicing \> Configuration \> Payments \> Bank Payment Profiles*

Steps:

1. Create a new profile and select the **Bank**.
2. Optionally link **Journals** to restrict the profile.
3. In the **Profile Lines**, define pairs of:
   - **Field**: A field on the `bank.payment.export` model.
   - **Value**: The default value. For `Many2one` / `Many2many`
     fields, use the record **ID** or **Name**. For `Selection`
     fields, use the exact technical value.
4. When a user selects this profile on a payment export, the system
   will **auto-fill** the corresponding field values.

> **Note:** Values must be valid (existing in the system). Invalid or
> incorrect entries will result in an error.
