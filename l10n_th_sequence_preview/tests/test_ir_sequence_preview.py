import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import Form, SingleTransactionCase


class TestIrSequencePreviewStandard(SingleTransactionCase):
    """ A few tests for a 'Standard' sequence. """

    def test_ir_sequence_preview_1_create(self):
        """ Create an ir.sequence record. """
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_preview",
                "name": "Test preview",
                "use_date_range": False,
                "prefix": "test-%(year)s/%(y)s/%(month)s/%(day)s-",
                "suffix": "-%(year)s/%(y)s/%(month)s/%(day)s",
                "padding": 4,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(seq)

    def test_ir_sequence_preview_2_change_date(self):
        domain = [("code", "=", "test_preview")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        year = fields.Date.today().year
        y = year % 100
        datetime1 = datetime.datetime(
            year=year, month=1, day=14, hour=10, minute=14, second=16, microsecond=0
        )
        with freeze_time(datetime1):
            seq._compute_preview()
            value = seq.preview
            self.assertEqual(value, f"test-{year}/{y}/01/14-0042-{year}/{y}/01/14")

        datetime2 = datetime.datetime(
            year=year, month=3, day=8, hour=10, minute=14, second=16, microsecond=0
        )
        with freeze_time(datetime2):
            seq._compute_preview()
            value = seq.preview
            self.assertEqual(value, f"test-{year}/{y}/03/08-0042-{year}/{y}/03/08")

    def test_ir_sequence_preview_3_change_prefix_suffix_padding(self):
        domain = [("code", "=", "test_preview")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        seq.prefix = "test-%(y)s/%(month)s-"
        seq.suffix = ""
        seq.padding = 5

        year = fields.Date.today().year
        y = year % 100
        datetime1 = datetime.datetime(
            year=year, month=1, day=14, hour=10, minute=14, second=16, microsecond=0
        )
        with freeze_time(datetime1):
            seq._compute_preview()
            value = seq.preview
            self.assertEqual(value, f"test-{y}/01-00042")

        datetime2 = datetime.datetime(
            year=year, month=3, day=8, hour=10, minute=14, second=16, microsecond=0
        )
        with freeze_time(datetime2):
            seq._compute_preview()
            value = seq.preview
            self.assertEqual(value, f"test-{y}/03-00042")

    def test_ir_sequence_preview_4_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_preview")])
        seq.unlink()


class TestIrSequencePreviewForm(SingleTransactionCase):
    """ Test with server-side form. """

    def test_ir_sequence_preview_form_1(self):
        """ Create a server-side form with an ir.sequence record. """
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_preview_form",
                "name": "Test preview",
                "use_date_range": False,
                "prefix": "test-%(y)s/%(month)s-",
                "padding": 4,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(seq)

        year = fields.Date.today().year
        y = year % 100
        datetime1 = datetime.datetime(
            year=year, month=1, day=14, hour=10, minute=14, second=16, microsecond=0
        )
        with freeze_time(datetime1):
            with Form(seq) as seq_form:
                self.assertTrue(seq_form.preview, f"test-{y}/01-0042")

                seq_form.padding = 5
                self.assertTrue(seq_form.preview, f"test-{y}/01-00042")

                seq_form.prefix = "test-%(doy)s-"
                self.assertTrue(seq_form.preview, f"test-14-00042")

                seq_form.save()

        seq.unlink()
