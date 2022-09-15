# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestIrSequenceQoyStandard(SingleTransactionCase):
    """A few tests for a 'Standard' sequence."""

    def test_ir_sequence_qoy_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_qoy",
                "name": "Test sequence QoY",
                "use_date_range": False,
                "prefix": "test-%(qoy)s-",
                "suffix": "-%(qoy)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

    def test_ir_sequence_qoy_2_change_date(self):
        year = fields.Date.today().year

        datetime1 = datetime.datetime(
            year=year - 1,
            month=11,
            day=14,
            hour=10,
            minute=14,
            second=16,
            microsecond=0,
        )
        with freeze_time(datetime1):
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-4-0001-4")
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-4-0002-4")

        datetime2 = datetime.datetime(
            year=year, month=3, day=14, hour=15, minute=9, second=26, microsecond=535898
        )
        with freeze_time(datetime2):
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-1-0003-1")
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-1-0004-1")

        datetime3 = datetime.datetime(
            year=year, month=5, day=21, hour=8, minute=19, second=37, microsecond=0
        )
        with freeze_time(datetime3):
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-2-0005-2")
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-2-0006-2")

        datetime4 = datetime.datetime(
            year=year, month=9, day=30, hour=22, minute=59, second=42, microsecond=0
        )
        with freeze_time(datetime4):
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-3-0007-3")
            value = self.env["ir.sequence"].next_by_code("test_qoy")
            self.assertEqual(value, "test-3-0008-3")

    def test_ir_sequence_qoy_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_qoy")])
        seq.unlink()


class TestIrSequenceQoyDateRange(SingleTransactionCase):
    """A few tests for a 'Standard' sequence with date_range."""

    def test_ir_sequence_qoy_date_range_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_qoy_date_range",
                "name": "Test sequence date_range QoY",
                "use_date_range": True,
                "prefix": "test-%(range_qoy)s-",
                "suffix": "-%(range_qoy)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

        year = fields.Date.today().year
        date_range_1 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year - 1, month=11, day=1),
                "date_to": datetime.date(year=year, month=1, day=31),
                "sequence_id": seq.id,
                "number_next_actual": 314,
            }
        )
        self.assertTrue(date_range_1)

        date_range_2 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year, month=2, day=1),
                "date_to": datetime.date(year=year, month=4, day=30),
                "sequence_id": seq.id,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(date_range_2)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(domain)
        self.assertEqual(len(date_ranges), 2)

    def test_ir_sequence_qoy_date_range_2_check_year(self):
        year = fields.Date.today().year

        datetime1 = datetime.datetime(
            year=year - 1,
            month=11,
            day=14,
            hour=10,
            minute=14,
            second=16,
            microsecond=0,
        )
        with freeze_time(datetime1):
            value = self.env["ir.sequence"].next_by_code("test_qoy_date_range")
            self.assertEqual(value, "test-4-0314-4")
            value = self.env["ir.sequence"].next_by_code("test_qoy_date_range")
            self.assertEqual(value, "test-4-0315-4")

        datetime2 = datetime.datetime(
            year=year, month=3, day=14, hour=15, minute=9, second=26, microsecond=535898
        )
        with freeze_time(datetime2):
            value = self.env["ir.sequence"].next_by_code("test_qoy_date_range")
            self.assertEqual(value, "test-1-0042-1")
            value = self.env["ir.sequence"].next_by_code("test_qoy_date_range")
            self.assertEqual(value, "test-1-0043-1")

    def test_ir_sequence_qoy_date_range_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_qoy_date_range")])
        seq.unlink()


class TestIrSequenceQoyRangeEnd(SingleTransactionCase):
    """A few tests for a 'Standard' sequence with range end."""

    def test_ir_sequence_qoy_range_end_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_qoy_range_end",
                "name": "Test sequence range end BE",
                "use_date_range": True,
                "prefix": "test-%(range_end_qoy)s-",
                "suffix": "-%(range_end_qoy)s",
                "padding": 4,
            }
        )
        self.assertTrue(seq)

        year = fields.Date.today().year
        date_range_1 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year - 1, month=11, day=1),
                "date_to": datetime.date(year=year, month=1, day=31),
                "sequence_id": seq.id,
                "number_next_actual": 314,
            }
        )
        self.assertTrue(date_range_1)

        date_range_2 = self.env["ir.sequence.date_range"].create(
            {
                "date_from": datetime.date(year=year, month=2, day=1),
                "date_to": datetime.date(year=year, month=4, day=30),
                "sequence_id": seq.id,
                "number_next_actual": 42,
            }
        )
        self.assertTrue(date_range_2)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(domain)
        self.assertEqual(len(date_ranges), 2)

    def test_ir_sequence_qoy_range_end_2_check_year(self):
        year = fields.Date.today().year

        datetime1 = datetime.datetime(
            year=year - 1,
            month=11,
            day=14,
            hour=10,
            minute=14,
            second=16,
            microsecond=0,
        )
        with freeze_time(datetime1):
            value = self.env["ir.sequence"].next_by_code("test_qoy_range_end")
            self.assertEqual(value, "test-1-0314-1")
            value = self.env["ir.sequence"].next_by_code("test_qoy_range_end")
            self.assertEqual(value, "test-1-0315-1")

        datetime2 = datetime.datetime(
            year=year, month=3, day=14, hour=15, minute=9, second=26, microsecond=535898
        )
        with freeze_time(datetime2):
            value = self.env["ir.sequence"].next_by_code("test_qoy_range_end")
            self.assertEqual(value, "test-2-0042-2")
            value = self.env["ir.sequence"].next_by_code("test_qoy_range_end")
            self.assertEqual(value, "test-2-0043-2")

    def test_ir_sequence_qoy_range_end_3_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_qoy_range_end")])
        seq.unlink()
