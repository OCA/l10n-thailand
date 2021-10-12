import datetime
from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import Form, SingleTransactionCase


class TestIrSequenceDateRangePreviewStandard(SingleTransactionCase):
    """ A few tests for a 'Standard' sequence. """

    def test_ir_sequence_date_range_preview_1_create(self):
        """ Create an ir.sequence record. """
        seq = self.env["ir.sequence"].create({
            "code": "test_date_range_preview",
            "name": "Test date_range preview",
            "use_date_range": True,
            "prefix": "test-%(range_y)s/%(range_month)s/%(range_day)s-",
            "suffix": "-%(range_y)s/%(range_month)s/%(range_day)s",
            "padding": 4,
        })
        self.assertTrue(seq)

        year = fields.Date.today().year
        date_range_1 = self.env["ir.sequence.date_range"].create({
            "date_from": datetime.date(year=year-1, month=11, day=1),
            "date_to": datetime.date(year=year, month=1, day=31),
            "sequence_id": seq.id,
            "number_next_actual": 314,
        })
        self.assertTrue(date_range_1)

        date_range_2 = self.env["ir.sequence.date_range"].create({
            "date_from": datetime.date(year=year, month=2, day=1),
            "date_to": datetime.date(year=year, month=4, day=30),
            "sequence_id": seq.id,
            "number_next_actual": 42,
        })
        self.assertTrue(date_range_2)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(domain)
        self.assertEqual(len(date_ranges), 2)

    def test_ir_sequence_date_range_preview_2_change_prefix_suffix_padding(self):
        domain = [("code", "=", "test_date_range_preview")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        year = fields.Date.today().year
        y = year % 100

        self.assertEqual(
            seq.date_range_ids[0].preview,
            f"test-{y-1}/11/01-0314-{y-1}/11/01"
        )
        self.assertEqual(
            seq.date_range_ids[1].preview,
            f"test-{y}/02/01-0042-{y}/02/01"
        )

        seq.padding = 5
        seq.date_range_ids._compute_preview()
        self.assertEqual(
            seq.date_range_ids[0].preview,
            f"test-{y-1}/11/01-00314-{y-1}/11/01"
        )
        self.assertEqual(
            seq.date_range_ids[1].preview,
            f"test-{y}/02/01-00042-{y}/02/01"
        )

        seq.prefix = "test-%(range_y)s/%(range_month)s-"
        seq.suffix = None
        seq.date_range_ids._compute_preview()
        self.assertEqual(
            seq.date_range_ids[0].preview,
            f"test-{y-1}/11-00314"
        )
        self.assertEqual(
            seq.date_range_ids[1].preview,
            f"test-{y}/02-00042"
        )

    def test_ir_sequence_date_range_preview_3_change_date(self):
        domain = [("code", "=", "test_date_range_preview")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)
        self.assertEqual(len(seq.date_range_ids), 2)

        seq.prefix = "test-%(range_y)s/%(range_month)s/%(range_day)s-"
        seq.suffix = None
        seq.padding = 3

        year = fields.Date.today().year
        y = year % 100
        seq.date_range_ids[0].date_from = datetime.date(year=year, month=5, day=1)
        seq.date_range_ids[0].date_to = datetime.date(year=year, month=7, day=31)
        seq.date_range_ids[1].date_from = datetime.date(year=year, month=8, day=1)
        seq.date_range_ids[1].date_to = datetime.date(year=year, month=10, day=30)
        seq.date_range_ids._compute_preview()
        self.assertEqual(
            seq.date_range_ids[0].preview,
            f"test-{y}/05/01-314"
        )
        self.assertEqual(
            seq.date_range_ids[1].preview,
            f"test-{y}/08/01-042"
        )

    def test_ir_sequence_date_range_preview_4_unlink(self):
        seq = self.env['ir.sequence'].search([('code', '=', 'test_date_range_preview')])
        seq.unlink()


class TestIrSequenceDateRangePreviewForm(SingleTransactionCase):
    """ Test with server-side form. """

    def test_ir_sequence_date_range_preview_form_1(self):
        """ Create a server-side form with an ir.sequence record. """
        seq = self.env["ir.sequence"].create({
            "code": "test_date_range_preview_form",
            "name": "Test preview",
            "use_date_range": True,
            "prefix": "test-%(range_y)s/%(range_month)s-",
            "padding": 4,
        })
        self.assertTrue(seq)

        year = fields.Date.today().year
        y = year % 100
        with Form(seq) as seq_form:
            with seq_form.date_range_ids.new() as date_range_1:
                date_range_1.date_from = datetime.date(year=year-1, month=11, day=1)
                date_range_1.date_to = datetime.date(year=year, month=1, day=31)
                date_range_1.number_next_actual = 314
            self.assertTrue(
                seq_form.date_range_ids.edit(0).preview,
                f"test-{y-1}/11-0314",
            )

            with seq_form.date_range_ids.new() as date_range_2:
                date_range_2.date_from = datetime.date(year=year, month=2, day=1)
                date_range_2.date_to = datetime.date(year=year, month=4, day=30)
                date_range_2.number_next_actual = 42
            self.assertTrue(
                seq_form.date_range_ids.edit(1).preview,
                f"test-{y}/02-0042",
            )

            seq_form.padding = 5
            self.assertTrue(
                seq_form.date_range_ids.edit(0).preview,
                f"test-{y-1}/11-00314",
            )
            self.assertTrue(
                seq_form.date_range_ids.edit(1).preview,
                f"test-{y}/02-00042",
            )

            seq_form.save()

        seq.unlink()
