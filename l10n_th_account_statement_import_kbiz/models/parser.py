"""Class to parse Kasikorn bank statement CSV files."""
# Copyright 2023 Ross Golder <ross@golder.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import csv
import datetime
import hashlib
import io
import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class KBizParser(models.AbstractModel):
    """Utility model for parsing KBiz statements"""

    _name = "account.statement.import.kbiz.parser"
    _description = "Account Bank Statement Import Kasikorn KBiz parser"

    def _prepare_transaction_line_kbiz_type1(self, invals):
        def _val(i):
            return float(i.replace(",", ""))

        # Parse date, labels and amounts
        dateval = invals[1]
        dateval = f"20{dateval[6:8]}-{dateval[3:5]}-{dateval[0:2]}"
        timeval = invals[1]
        label1 = invals[3]
        label2 = invals[12]
        try:
            debit = 0.0 - _val(invals[4])
        except ValueError:
            debit = 0.0
        try:
            credit = _val(invals[6])
        except ValueError:
            credit = 0.0
        amount = debit + credit
        balance = invals[8]

        hashkey = "".join([dateval, timeval, label1, label2, str(amount), balance])
        hashval = hashlib.sha256(hashkey.encode("utf-8"))

        vals = {
            "date": dateval,
            "ref": label1,
            "payment_ref": label2,
            "amount": float(amount),
            "unique_import_id": hashval.hexdigest(),
        }
        return vals

    def parse_statement(self, data):
        """Parse a KBiz CSV statement file."""
        try:
            sio = io.StringIO(data.decode("utf8"))
            reader = csv.reader(sio, quotechar='"')
        except Exception as exc:
            _logger.error(exc)
            return False

        statement = {}
        transactions = []
        start_date = None
        end_date = None

        rowcount = 0
        for values in reader:
            rowcount += 1

            # Check initial rows for signature cells
            signaturetext = "\ufeffรายการเดินบัญชีเงินฝากออมทรัพย์ (มีรายละเอียด)"
            if rowcount == 1 and values[0] != signaturetext:
                _logger.info(_("Not identified as a KBiz statement (CSV type1)"))
                return False

            # Grab declared period for end date
            if rowcount == 6:
                period = values[11]
                startdate = period[0:10]
                start_date = datetime.datetime.strptime(startdate, "%d/%m/%Y").strftime(
                    "%Y-%m-%d"
                )
                enddate = period[13:]
                end_date = datetime.datetime.strptime(enddate, "%d/%m/%Y").strftime(
                    "%Y-%m-%d"
                )

            # Determine balances as stated
            if rowcount == 8:
                ending_balance = float(values[12].replace(",", ""))
            if rowcount == 9:
                total_withdrawals = float(values[12].replace(",", ""))
                count_withdrawals = int(values[9])
            if rowcount == 10:
                total_deposits = float(values[12].replace(",", ""))
                count_deposits = int(values[9])
                start_balance = ending_balance - total_deposits + total_withdrawals
                statement["balance_start"] = start_balance
                statement["balance_end_real"] = ending_balance

            # Discard remaining header lines
            if rowcount < 13:
                continue

            # Check remaining statement lines have expected number of columns
            if len(values) != 13:
                _logger.warning(_("Wrong number of columns on line (%s)", len(values)))
                continue

            # Add this statement line to our results
            transactions.append(self._prepare_transaction_line_kbiz_type1(values))

        # Error if we didn't extract the expected number of transactions
        if count_deposits + count_withdrawals != len(transactions):
            raise Exception(
                _(
                    "Unexpected number of transaction rows harvested (%d != %d)",
                    count_deposits + count_withdrawals,
                    len(transactions),
                )
            )

        statement["name"] = start_date[0:7]
        statement["date"] = end_date
        statement["transactions"] = transactions

        return statement

    def parse(self, data):
        """Parse a KBiz CSV statement file."""
        statement = self.parse_statement(data)

        # Account number is masked in download, so cannot be included
        return self.env.ref("base.THB").name, None, [statement]

    def _parse_file(self, data_file):
        # If we can't read it, pass it to next handler
        stmtdata = self._read_file_kbiz_type1(data_file)
        if not stmtdata:
            return super()._parse_file(data_file)

        # Calculate balance from raw data, and drop any transactions
        # that have already been imported
        transactions = []
        total_amt = 0.00
        lineno = 0
        for vals in stmtdata["transactions"]:
            lineno += 1
            total_amt += float(vals["amount"])
            tx1 = dict(vals)
            already_imported = self.env["account.statement.line"].search(
                {[{"unique_import_id", "=", tx1["unique_import_id"]}]}
            )
            if len(already_imported) > 0:
                _logger.warning(_("Statement line %d was already imported", lineno))
                continue
            transactions.append(tx1)
        stmtdata["transactions"] = transactions

        return stmtdata
