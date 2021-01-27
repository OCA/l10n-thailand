from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestHrEmployeeIdValidation(TransactionCase):
    def setUp(self):
        super(TestHrEmployeeIdValidation, self).setUp()
        self.employee = self.env["hr.employee"].create(
            {"name": "Piruin Panichphol", "country_id": self.ref("base.th")}
        )

    def test_not_validate_id_when_change_country(self):
        self.employee.update(
            {"country_id": self.ref("base.us"), "identification_id": "123"}
        )
        self.assertEqual(self.employee.identification_id, "123")

    def test_validate_id_when_change_country_to_thai(self):
        self.employee.update(
            {"country_id": None, "identification_id": "auto-generated-id"}
        )
        with self.assertRaises(UserError):
            self.employee.country_id = self.ref("base.th")

    def test_invalid_format(self):
        with self.assertRaises(UserError):
            self.employee.identification_id = "1"
        with self.assertRaises(UserError):
            self.employee.identification_id = "12345678910234"

    def test_valid_id(self):
        self.employee.identification_id = "1610255800005"
        self.assertEqual(self.employee.identification_id, "1610255800005")

        self.employee.identification_id = "1610255811112"
        self.assertEqual(self.employee.identification_id, "1610255811112")

        self.employee.identification_id = "1610255822220"
        self.assertEqual(self.employee.identification_id, "1610255822220")

    def test_invalid_checksum(self):
        with self.assertRaises(UserError):
            self.employee.identification_id = "0012300000000"
        with self.assertRaises(UserError):
            self.employee.identification_id = "1345678981235"
        with self.assertRaises(UserError):
            self.employee.identification_id = "1101401424854"

    def test_not_preprocess_identification_id(self):
        self.employee.update(
            {
                "country_id": self.ref("base.us"),
                "identification_id": "1 6102 55811 11 2",
            }
        )
        self.assertEqual(self.employee.identification_id, "1 6102 55811 11 2")

    def test_preprocess_identification_id(self):
        self._force_preprocess_id(self.employee, "1 6102 55811 11 2   ")
        self.assertEqual(self.employee.identification_id, "1610255811112")

        self._force_preprocess_id(self.employee, "1-6102-55811-11-2   ")
        self.assertEqual(self.employee.identification_id, "1610255811112")

        self._force_preprocess_id(self.employee, " a12 bc 34de 5%")
        self.assertEqual(self.employee.identification_id, "12345")

    def _force_preprocess_id(self, employee, new_id):
        try:
            employee.identification_id = new_id
        except UserError:
            try:
                employee._preprocess_identification_id()
            except UserError:
                pass
        return self
