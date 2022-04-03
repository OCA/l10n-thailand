from odoo.addons.base.tests.test_ir_sequence_date_range import (
    TestIrSequenceDateRangeChangeImplementation,
    TestIrSequenceDateRangeNoGap,
    TestIrSequenceDateRangeStandard,
)


class TestIrSequenceDateRangeRefactoredStandard(TestIrSequenceDateRangeStandard):
    """
    This module refactors the `_get_prefix_suffix()` method from the codebase without
    modifying/extending its functionalities. Therefore, this module is tested by rerun
    all existing tests in the `ir.sequence.date_range` codebase.
    """

    def setUp(self):
        """Rerun the 'standard' test from the base's ir.sequence.date_range"""
        super(TestIrSequenceDateRangeRefactoredStandard, self).setUp()


class TestIrSequenceDateRangeRefactoredNoGap(TestIrSequenceDateRangeNoGap):
    """Rerun the 'no gap' test from the base's ir.sequence.date_range"""

    def setUp(self):
        """Run the 'no gap' test"""
        super(TestIrSequenceDateRangeRefactoredNoGap, self).setUp()


class TestIrSequenceDateRangeRefactoredChangeImplementation(
    TestIrSequenceDateRangeChangeImplementation
):
    """Rerun the 'change implementation' test from the base's ir.sequence.date_range"""

    def setUp(self):
        """Run the 'change implementation' test"""
        super(TestIrSequenceDateRangeRefactoredChangeImplementation, self).setUp()
