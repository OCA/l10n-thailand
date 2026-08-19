# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        required=True,
    )
    wht_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        required=True,
    )
    wht_text_file_pnd1_format = fields.Text(
        string="Layout in Text File PND1",
        help="Display format to use for text file PND1.\n\n"
        "You can use python-style string pattern with all the fields "
        "of the withholding tax (for example, "
        "use '%(partner_vat)s' to display the field 'partner_vat') plus"
        "\n%(row_number)s: Index"
        "\n%(cert_cancel)s: Cancelled"
        "\n%(cert_date)s: Date"
        "\n%(cert_date_str)s: Date (string)"
        "\n%(cert_name)s: Name"
        "\n%(cert_tax_payer)s: Tax Payer"
        "\n%(cert_tax_payer_display)s: Tax Payer Display"
        "\n%(cert_tax_payer_code)s: Tax Payer Code"
        "\n%(partner_id)s: Partner ID"
        "\n%(partner_name)s: Partner Name"
        "\n%(partner_title)s: Partner Title"
        "\n%(partner_firstname)s: Partner Firstname"
        "\n%(partner_lastname)s: Partner Lastname"
        "\n%(partner_address)s: Partner Address"
        "\n%(partner_street)s: Partner Street"
        "\n%(partner_street2)s: Partner Street2"
        "\n%(partner_city)s: Partner City"
        "\n%(partner_state)s: Partner State"
        "\n%(partner_zip)s: Partner Zip"
        "\n%(partner_country)s: Partner Country"
        "\n%(partner_vat)s: Partner VAT"
        "\n%(partner_branch)s: Partner Branch"
        "\n%(partner_bank_account)s: Partner Bank Account"
        "\n%(income_code)s: Income Code"
        "\n%(base)s: Base"
        "\n%(amount)s: Amount",
        default="%(income_code)s|%(row_number)s|%(partner_vat)s|%(partner_title)s|%(partner_firstname)s|%(partner_lastname)s|%(cert_date)s|%(base)s|%(amount)s|%(cert_tax_payer)s\n",
    )
    wht_text_file_pnd3_format = fields.Text(
        string="Layout in Text File PND3",
        help="Display format to use for text file PND3.\n\n"
        "You can use python-style string pattern with all the fields "
        "of the withholding tax (for example, "
        "use '%(partner_vat)s' to display the field 'partner_vat') plus"
        "\n%(row_number)s: Index"
        "\n%(cert_cancel)s: Cancelled"
        "\n%(cert_date)s: Date"
        "\n%(cert_date_str)s: Date (string)"
        "\n%(cert_name)s: Name"
        "\n%(cert_tax_payer)s: Tax Payer"
        "\n%(cert_tax_payer_display)s: Tax Payer Display"
        "\n%(cert_tax_payer_code)s: Tax Payer Code"
        "\n%(partner_id)s: Partner ID"
        "\n%(partner_name)s: Partner Name"
        "\n%(partner_title)s: Partner Title"
        "\n%(partner_firstname)s: Partner Firstname"
        "\n%(partner_lastname)s: Partner Lastname"
        "\n%(partner_address)s: Partner Address"
        "\n%(partner_street)s: Partner Street"
        "\n%(partner_street2)s: Partner Street2"
        "\n%(partner_city)s: Partner City"
        "\n%(partner_state)s: Partner State"
        "\n%(partner_zip)s: Partner Zip"
        "\n%(partner_country)s: Partner Country"
        "\n%(partner_vat)s: Partner VAT"
        "\n%(partner_branch)s: Partner Branch"
        "\n%(partner_bank_account)s: Partner Bank Account"
        "\n%(income_code)s: Income Code"
        "\n%(base)s: Base"
        "\n%(amount)s: Amount",
        default="%(row_number)s|%(partner_vat)s|%(partner_branch)s|%(partner_title)s|%(partner_firstname)s|%(partner_lastname)s|%(partner_street)s|%(partner_street2)s|%(partner_city)s|%(partner_state)s|%(partner_zip)s|%(loop_cert_date)s|%(loop_wht_cert_income_desc)s|%(loop_wht_percent)s|%(loop_base)s|%(loop_amount)s|%(loop_cert_tax_payer)s\n",
    )
    wht_text_file_pnd53_format = fields.Text(
        string="Layout in Text File PND53",
        help="Display format to use for text file PND53.\n\n"
        "You can use python-style string pattern with all the fields "
        "of the withholding tax (for example, "
        "use '%(partner_vat)s' to display the field 'partner_vat') plus"
        "\n%(row_number)s: Index"
        "\n%(cert_cancel)s: Cancelled"
        "\n%(cert_date)s: Date"
        "\n%(cert_date_str)s: Date (string)"
        "\n%(cert_name)s: Name"
        "\n%(cert_tax_payer)s: Tax Payer"
        "\n%(cert_tax_payer_display)s: Tax Payer Display"
        "\n%(cert_tax_payer_code)s: Tax Payer Code"
        "\n%(partner_id)s: Partner ID"
        "\n%(partner_name)s: Partner Name"
        "\n%(partner_title)s: Partner Title"
        "\n%(partner_firstname)s: Partner Firstname"
        "\n%(partner_lastname)s: Partner Lastname"
        "\n%(partner_address)s: Partner Address"
        "\n%(partner_street)s: Partner Street"
        "\n%(partner_street2)s: Partner Street2"
        "\n%(partner_city)s: Partner City"
        "\n%(partner_state)s: Partner State"
        "\n%(partner_zip)s: Partner Zip"
        "\n%(partner_country)s: Partner Country"
        "\n%(partner_vat)s: Partner VAT"
        "\n%(partner_branch)s: Partner Branch"
        "\n%(partner_bank_account)s: Partner Bank Account"
        "\n%(income_code)s: Income Code"
        "\n%(base)s: Base"
        "\n%(amount)s: Amount",
        default="%(row_number)s|%(partner_vat)s|%(partner_branch)s|%(partner_title)s|%(partner_name)s|%(partner_street)s|%(partner_street2)s|%(partner_city)s|%(partner_state)s|%(partner_zip)s|%(loop_cert_date)s|%(loop_wht_cert_income_desc)s|%(loop_wht_percent)s|%(loop_base)s|%(loop_amount)s|%(loop_cert_tax_payer)s\n",
    )
