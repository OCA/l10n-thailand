import datetime

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestIrSequenceRangeEndStandard(SingleTransactionCase):
    """ A few tests for a "Standard' sequence with date_range. """

    def test_ir_sequence_range_end_1_create(self):
        """Create an ir.sequence record with two ir.sequence.date_range records"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_range_end",
                "name": "Test range end",
                "use_date_range": True,
                "prefix": "test-%(year)s/%(range_year)s/%(range_end_year)s-",
                "suffix": "-%(y)s/%(range_y)s/%(range_end_y)s",
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

    def test_ir_sequence_range_end_2_check_year(self):
        year = fields.Date.today().year
        y = year % 100
        date1 = datetime.date(year=year, month=1, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-{year}/{year-1}/{year}-0314-{y}/{y-1}/{y}")
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-{year}/{year-1}/{year}-0315-{y}/{y-1}/{y}")

        date2 = datetime.date(year=year, month=3, day=14)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-{year}/{year}/{year}-0042-{y}/{y}/{y}")
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-{year}/{year}/{year}-0043-{y}/{y}/{y}")

    def test_ir_sequence_range_end_3_check_month(self):
        domain = [("code", "=", "test_range_end")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        seq.prefix = "test-%(month)s/%(range_month)s/%(range_end_month)s-"
        seq.suffix = "-%(month)s/%(range_month)s/%(range_end_month)s"
        seq.padding = 3

        year = fields.Date.today().year
        date1 = datetime.date(year=year - 1, month=12, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-12/11/01-316-12/11/01")
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-12/11/01-317-12/11/01")

        date2 = datetime.date(year=year, month=4, day=30)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-04/02/04-044-04/02/04")
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-04/02/04-045-04/02/04")

    def test_ir_sequence_range_end_4_check_day(self):
        domain = [("code", "=", "test_range_end")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        seq.prefix = "test-%(day)s/%(range_day)s/%(range_end_day)s-"
        seq.suffix = "-%(day)s/%(range_day)s/%(range_end_day)s"
        seq.padding = 5

        year = fields.Date.today().year
        date1 = datetime.date(year=year - 1, month=11, day=1)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-01/01/31-00318-01/01/31")
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-01/01/31-00319-01/01/31")

        date2 = datetime.date(year=year, month=4, day=13)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-13/01/30-00046-13/01/30")
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-13/01/30-00047-13/01/30")

    def test_ir_sequence_range_end_5_change_date(self):
        domain = [("code", "=", "test_range_end")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(
            domain, order="date_from"
        )
        self.assertEqual(len(date_ranges), 2)

        seq.prefix = "test-%(month)s/%(range_month)s/%(range_end_month)s-"
        seq.suffix = "-%(day)s/%(range_day)s/%(range_end_day)s"
        seq.padding = 3

        year = fields.Date.today().year
        date_ranges[0].date_from = datetime.date(year=year, month=5, day=1)
        date_ranges[0].date_to = datetime.date(year=year, month=7, day=31)
        date_ranges[1].date_from = datetime.date(year=year, month=8, day=1)
        date_ranges[1].date_to = datetime.date(year=year, month=10, day=30)

        date1 = datetime.date(year=year, month=6, day=5)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-06/05/07-320-05/01/31")
        value = seq1.next_by_code("test_range_end")
        self.assertEqual(value, f"test-06/05/07-321-05/01/31")

        date2 = datetime.date(year=year, month=9, day=22)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-09/08/10-048-22/01/30")
        value = seq2.next_by_code("test_range_end")
        self.assertEqual(value, f"test-09/08/10-049-22/01/30")

    def test_ir_sequence_range_end_6_unlink(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_range_end")])
        seq.unlink()


class TestIrSequenceRangeEndNoGap(SingleTransactionCase):
    """ Copy of the previous tests for a 'No gap' sequence. """

    def test_ir_sequence_range_end_1_create_no_gap(self):
        """Create a sequence with date_range"""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_range_end_no_gap",
                "name": "Test range end no gap",
                "use_date_range": True,
                "implementation": "no_gap",
                "prefix": "test-%(year)s/%(range_year)s/%(range_end_year)s-",
                "suffix": "-%(y)s/%(range_y)s/%(range_end_y)s",
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

    def test_ir_sequence_range_end_2_check_year_no_gap(self):
        year = fields.Date.today().year
        y = year % 100
        date1 = datetime.date(year=year, month=1, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-{year}/{year-1}/{year}-0314-{y}/{y-1}/{y}")
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-{year}/{year-1}/{year}-0315-{y}/{y-1}/{y}")

        date2 = datetime.date(year=year, month=3, day=14)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-{year}/{year}/{year}-0042-{y}/{y}/{y}")
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-{year}/{year}/{year}-0043-{y}/{y}/{y}")

    def test_ir_sequence_range_end_3_check_month_no_gap(self):
        domain = [("code", "=", "test_range_end_no_gap")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        seq.prefix = "test-%(month)s/%(range_month)s/%(range_end_month)s-"
        seq.suffix = "-%(month)s/%(range_month)s/%(range_end_month)s"
        seq.padding = 3

        year = fields.Date.today().year
        date1 = datetime.date(year=year - 1, month=12, day=14)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-12/11/01-316-12/11/01")
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-12/11/01-317-12/11/01")

        date2 = datetime.date(year=year, month=4, day=30)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-04/02/04-044-04/02/04")
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-04/02/04-045-04/02/04")

    def test_ir_sequence_range_end_4_check_day_no_gap(self):
        domain = [("code", "=", "test_range_end_no_gap")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        seq.prefix = "test-%(day)s/%(range_day)s/%(range_end_day)s-"
        seq.suffix = "-%(day)s/%(range_day)s/%(range_end_day)s"
        seq.padding = 5

        year = fields.Date.today().year
        date1 = datetime.date(year=year - 1, month=11, day=1)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-01/01/31-00318-01/01/31")
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-01/01/31-00319-01/01/31")

        date2 = datetime.date(year=year, month=4, day=13)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-13/01/30-00046-13/01/30")
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-13/01/30-00047-13/01/30")

    def test_ir_sequence_range_end_5_change_date_no_gap(self):
        domain = [("code", "=", "test_range_end_no_gap")]
        seq = self.env["ir.sequence"].search(domain)
        self.assertEqual(len(seq), 1)

        domain = [("sequence_id", "=", seq.id)]
        date_ranges = self.env["ir.sequence.date_range"].search(
            domain, order="date_from"
        )
        self.assertEqual(len(date_ranges), 2)

        seq.prefix = "test-%(month)s/%(range_month)s/%(range_end_month)s-"
        seq.suffix = "-%(day)s/%(range_day)s/%(range_end_day)s"
        seq.padding = 3

        year = fields.Date.today().year
        date_ranges[0].date_from = datetime.date(year=year, month=5, day=1)
        date_ranges[0].date_to = datetime.date(year=year, month=7, day=31)
        date_ranges[1].date_from = datetime.date(year=year, month=8, day=1)
        date_ranges[1].date_to = datetime.date(year=year, month=10, day=31)

        date1 = datetime.date(year=year, month=6, day=5)
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-06/05/07-320-05/01/31")
        value = seq1.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-06/05/07-321-05/01/31")

        date2 = datetime.date(year=year, month=9, day=22)
        seq2 = self.env["ir.sequence"].with_context(ir_sequence_date=date2)
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-09/08/10-048-22/01/31")
        value = seq2.next_by_code("test_range_end_no_gap")
        self.assertEqual(value, f"test-09/08/10-049-22/01/31")

    def test_ir_sequence_range_end_6_unlink_no_gap(self):
        seq = self.env["ir.sequence"].search([("code", "=", "test_range_end_no_gap")])
        seq.unlink()


class TestIrSequenceRangeEndChangeImplementation(SingleTransactionCase):
    """ Create sequence objects and change their ``implementation`` field. """

    def test_ir_sequence_range_end_1_create(self):
        """ Try to create sequence objects. """
        seq3 = self.env["ir.sequence"].create(
            {
                "code": "test_range_end_3",
                "name": "Test sequence 3",
                "use_date_range": True,
            }
        )
        self.assertTrue(seq3)

        seq4 = self.env["ir.sequence"].create(
            {
                "code": "test_range_end_4",
                "name": "Test sequence 4",
                "use_date_range": True,
                "implementation": "no_gap",
            }
        )
        self.assertTrue(seq4)

    def test_ir_sequence_range_end_2_use(self):
        """ Make some use of the sequences to create some subsequences """
        year = fields.Date.today().year

        date1 = datetime.date(year=year - 1, month=1, day=14)
        seq = self.env["ir.sequence"]
        seq1 = self.env["ir.sequence"].with_context(ir_sequence_date=date1)

        for i in range(1, 5):
            value = seq.next_by_code("test_range_end_3")
            self.assertEqual(value, str(i))
        for i in range(1, 5):
            value = seq1.next_by_code("test_range_end_3")
            self.assertEqual(value, str(i))
        for i in range(1, 5):
            value = seq.next_by_code("test_range_end_4")
            self.assertEqual(value, str(i))
        for i in range(1, 5):
            value = seq1.next_by_code("test_range_end_4")
            self.assertEqual(value, str(i))

    def test_ir_sequence_range_end_3_write(self):
        """swap the implementation method on both"""
        domain = [("code", "in", ["test_range_end_3", "test_range_end_4"])]
        seqs = self.env["ir.sequence"].search(domain)
        seqs.write({"implementation": "standard"})
        seqs.write({"implementation": "no_gap"})

    def test_ir_sequence_range_end_4_unlink(self):
        domain = [("code", "in", ["test_range_end_3", "test_range_end_4"])]
        seqs = self.env["ir.sequence"].search(domain)
        seqs.unlink()
