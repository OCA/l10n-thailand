Choose a KBank template, the transfer product, the effective date and the
charge bearer, then add payments and export the text file.

The standard format follows `KBank_Excel Template_V2.6.2.xlsm`:

- Same-bank products: FTR, FTL, DCT and PCT.
- Other-bank products: MCL, MCS, BNL, PCL and IPP.
- Both supplied templates set File Encoding to Windows-874 (Thai ANSI).
  File Encoding and Line Ending are configured on the bank template in the
  base bank payment export module. The downloaded file uses CRLF and
  preserves literal characters such as `&` instead of HTML entities.
- SMS is optional. Set the SMS language when providing a number. Payroll
  products PCT/PCL include SMS only when WHT information is present.
- Standard WHT exports one T record per certificate line, up to three per
  payment, with sequential tax numbers starting at 1. Cancelled certificates
  are excluded. FTR does not export WHT. This format does not implement e-WHT
  or the bank's Single Payment Format.
- MCL/MCS/PCL accounts are padded with leading zeroes to 20 characters;
  BNL/IPP accounts are padded with trailing spaces. Branch codes follow the
  workbook rules, including GSB's `9990` and IPP's default `9999`.

Upgrade this module after deploying the changes so the existing template
records are refreshed from the CSV data. Review any locally customized
standard template records before upgrading.
