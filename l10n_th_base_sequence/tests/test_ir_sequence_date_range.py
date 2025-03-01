# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import TransactionCase, freeze_time, patch


class TestIrSequenceDateRangePreviewStandard(TransactionCase):
    def test_pseudo_record_standard_sequence(self):
        """Test that _predict_nextval() is called for sequences on pseudo records"""
        sequence_standard = self.env["ir.sequence"].create(
            {
                "name": "Test Standard Sequence",
                "implementation": "standard",
            }
        )
        record_pseudo = self.env["ir.sequence.date_range"].new(
            {
                "sequence_id": sequence_standard.id,
                "number_next": 20,
            }
        )

        with patch(
            "odoo.addons.l10n_th_base_sequence.models.ir_sequence_date_range._predict_nextval",
            return_value=42,
        ) as mock_predict:
            record_pseudo._get_number_next_actual()
            expected_seq_id = "%03d_%03d" % (
                sequence_standard._origin.id,
                record_pseudo._origin.id,
            )
            mock_predict.assert_called_once_with(record_pseudo, expected_seq_id)
            self.assertEqual(record_pseudo.number_next_actual, 42)

    @freeze_time("2001-02-01")
    def test_ir_sequence_date_range_preview(self):
        """Create an ir.sequence record."""
        seq = self.env["ir.sequence"].create(
            {
                "code": "test_date_range_preview",
                "name": "Test date_range preview",
                "use_date_range": True,
                "prefix": "test-%(range_y)s/%(range_month)s/%(range_day)s-",
                "suffix": "-%(range_y)s/%(range_month)s/%(range_day)s",
                "padding": 4,
                "date_range_ids": [
                    (
                        0,
                        0,
                        {
                            "date_from": "2001-01-01",
                            "date_to": "2001-12-31",
                            "number_next_actual": 314,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "date_from": "2002-01-01",
                            "date_to": "2002-12-31",
                            "number_next_actual": 42,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(seq.date_range_ids[0].preview, "test-01/01/01-0314-01/01/01")
        self.assertEqual(seq.date_range_ids[1].preview, "test-02/01/01-0042-02/01/01")

        # Check change sequence padding, preview should change too
        seq.write({"padding": 5, "implementation": "no_gap"})
        self.env.clear()  # discard cache and pending recomputations
        self.assertEqual(seq.date_range_ids[0].preview, "test-01/01/01-00314-01/01/01")
        self.assertEqual(seq.date_range_ids[1].preview, "test-02/01/01-00042-02/01/01")
        next_number = seq.date_range_ids[0]._next()
        self.assertEqual(next_number, "test-01/02/01-00314-01/02/01")
        self.assertFalse(seq.preview)
