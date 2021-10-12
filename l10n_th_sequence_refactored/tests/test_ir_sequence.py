from odoo.tests import TransactionCase
from odoo.addons.base.tests.test_ir_sequence import TestIrSequenceStandard, \
    TestIrSequenceNoGap, TestIrSequenceChangeImplementation, TestIrSequenceGenerate, \
    TestIrSequenceInit


class TestIrSequenceRefactoredStandard(TestIrSequenceStandard):
    """
    This module refactors the `_get_prefix_suffix()` method from the codebase without
    modifying/extending its functionalities. Therefore, this module is tested by rerun
    all existing tests in the `ir.sequence` codebase.
    """

    def setUp(self):
        """Rerun the 'standard' test from the base's ir.sequence"""
        super(TestIrSequenceRefactoredStandard, self).setUp()


class TestIrSequenceRefactoredNoGap(TestIrSequenceNoGap):
    """ Rerun the 'no gap' test from the base's ir.sequence """

    def setUp(self):
        """ Run the 'no gap' test """
        super(TestIrSequenceRefactoredNoGap, self).setUp()


class TestIrSequenceRefactoredChangeImplementation(TestIrSequenceChangeImplementation):
    """ Rerun the 'change implementation' test from the base's ir.sequence """

    def setUp(self):
        """Run the 'change implementation' test """
        super(TestIrSequenceRefactoredChangeImplementation, self).setUp()


class TestIrSequenceRefactoredGenerate(TestIrSequenceGenerate):
    """ Rerun the 'generate' test from the base's ir.sequence """

    def setUp(self):
        """Run the 'generate' test """
        super(TestIrSequenceRefactoredGenerate, self).setUp()


class TestIrSequenceRefactoredInit(TestIrSequenceInit):
    """ Rerun the 'init' test from the base's ir.sequence """

    def setUp(self):
        """ Run the 'init' test """
        super(TestIrSequenceRefactoredInit, self).setUp()
