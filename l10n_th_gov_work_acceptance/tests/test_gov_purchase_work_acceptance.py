# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestGovPurchaseWorkAcceptance(TransactionCase):
    def setUp(self):
        super().setUp()
        # Model
        self.purchase_request_model = self.env["purchase.request"]
        self.purchase_order_model = self.env["purchase.order"]
        self.procurement_committee_model = self.env["procurement.committee"]
        self.config_setting = self.env["res.config.settings"]
        self.wiz = self.env["purchase.request.line.make.purchase.requisition"]
        # Data Test
        self.product1 = self.env.ref("product.product_product_7")
        self.procurement_type1 = self.env.ref(
            "l10n_th_gov_purchase_request.procurement_type_001"
        )
        self.procurement_method1 = self.env.ref(
            "l10n_th_gov_purchase_request.procurement_specific"
        )
        self.purchase_type3 = self.env.ref(
            "l10n_th_gov_purchase_request.purchase_type_003"
        )
        self.pr_exception = self.env.ref("l10n_th_gov_purchase_request.pr_exception_4")
        self.employee = self.env.ref("base.user_demo")
        self.employee1 = self.env.ref("hr.employee_hne")
        self.employee2 = self.env.ref("hr.employee_lur")
        self.employee3 = self.env.ref("hr.employee_jgo")
        self.res_partner = self.env.ref("base.res_partner_12")
        self.date_now = fields.Datetime.now()
        self.main_company = self.env.ref("base.main_company")

        # Enable WA Evaluation
        with Form(self.config_setting) as c:
            c.group_enable_eval_on_wa = True
            c.save()
        self.config_setting.create({"group_enable_eval_on_wa": True}).execute()

    def _create_work_acceptance(self, qty, po=False, committees=False):
        work_acceptance = self.env["work.acceptance"].create(
            {
                "purchase_id": po and po.id or False,
                "partner_id": self.res_partner.id,
                "responsible_id": self.employee.id,
                "date_due": self.date_now,
                "date_receive": self.date_now,
                "company_id": self.main_company.id,
                "wa_line_ids": [
                    (
                        0,
                        0,
                        {
                            "purchase_line_id": po and po.order_line[0].id or False,
                            "product_id": po
                            and po.order_line[0].product_id.id
                            or self.service_product.id,
                            "name": po
                            and po.order_line[0].name
                            or self.service_product.name,
                            "price_unit": po
                            and po.order_line[0].price_unit
                            or self.service_product.standard_price,
                            "product_uom": po
                            and po.order_line[0].product_uom.id
                            or self.service_product.uom_id.id,
                            "product_qty": qty,
                        },
                    )
                ],
                "work_acceptance_committee_ids": committees,
            }
        )
        return work_acceptance

    def test_01_gov_purchase_request_to_work_acceptance(self):
        """Process Purchase Request until work acceptance and committee must approve WA"""
        committees = [
            (
                0,
                0,
                {
                    "employee_id": self.employee1.id,
                    "approve_role": "chairman",
                    "committee_type": "work_acceptance",
                },
            ),
            (
                0,
                0,
                {
                    "employee_id": self.employee2.id,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                },
            ),
            (
                0,
                0,
                {
                    "employee_id": self.employee3.id,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                },
            ),
        ]
        purchase_request = self.purchase_request_model.create(
            {
                "procurement_type_id": self.procurement_type1.id,
                "procurement_method_id": self.procurement_method1.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "estimated_cost": 100.0,
                            "product_qty": 1,
                            "product_id": self.product1.id,
                            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
                "work_acceptance_committee_ids": committees,
            }
        )
        purchase_request.button_to_approve()
        purchase_request.with_context(to_substate_sequence=20).action_to_substate()
        purchase_request.button_approved()
        # Create purchase agreement from purchase request
        wiz = self.wiz.with_context(
            active_model="purchase.request.line",
            active_ids=[purchase_request.line_ids.id],
            active_id=purchase_request.line_ids.id,
        ).create({})
        wiz.make_purchase_requisition()
        purchase_request_line = purchase_request.line_ids
        requisition = purchase_request_line.requisition_lines.requisition_id
        requisition_line = requisition.line_ids
        requisition_line.price_unit = 100.0
        requisition.action_in_progress()
        requisition.action_open()
        # Create Purchase from Agreement
        purchase = self.purchase_order_model.create(
            {
                "partner_id": self.res_partner.id,
                "requisition_id": requisition.id,
            }
        )
        purchase._onchange_requisition_id()
        purchase.button_confirm()
        # Check WA default
        res = purchase.with_context(create_wa=True).action_view_wa()
        ctx = res.get("context")
        work_acceptance = Form(self.env["work.acceptance"].with_context(**ctx))
        self.assertEqual(work_acceptance.state, "draft")
        self.assertEqual(len(work_acceptance.work_acceptance_committee_ids), 3)
        self.assertTrue(work_acceptance.wa_tier_validation)
        for committee in committees:
            del committee[2]["committee_type"]
        work_acceptance = self._create_work_acceptance(1, purchase, committees)
        eval_resuls = work_acceptance.evaluation_result_ids
        # Set score evaluation
        eval_resuls[0].score_id = eval_resuls[0].case_id.score_ids[0]
        eval_resuls[1].score_id = eval_resuls[1].case_id.score_ids[0]
        eval_resuls[2].score_id = eval_resuls[2].case_id.score_ids[0]
        eval_resuls[3].score_id = eval_resuls[3].case_id.score_ids[0]
        eval_resuls[4].score_id = eval_resuls[4].case_id.score_ids[0]
        eval_resuls[5].score_id = eval_resuls[5].case_id.score_ids[0]
        # Paperless must tier validation first
        with self.assertRaises(ValidationError):
            work_acceptance.button_accept()
        # Check exception in process tier validation
        res = work_acceptance._get_under_validation_exceptions()
        self.assertEqual("evaluation_result_ids", res[-1])
        # Start Tier Validation
        work_acceptance.request_validation()
        work_acceptance.invalidate_cache()  # Needed to refresh review_ids field
        work_acceptance.review_ids.write({"status": "approved"})
        # Normally, this function will automate from tier server action
        work_acceptance.work_acceptance_committee_ids.write({"status": "accept"})
        self.assertEqual(work_acceptance.completeness, 100.0)
        # Test restart tier, status and note must be clear
        self.assertTrue(work_acceptance.work_acceptance_committee_ids[0].status)
        work_acceptance.restart_validation()
        self.assertFalse(work_acceptance.work_acceptance_committee_ids[0].status)

        work_acceptance.request_validation()
        work_acceptance.invalidate_cache()  # Needed to refresh review_ids field
        work_acceptance.review_ids.write({"status": "approved"})
        work_acceptance.work_acceptance_committee_ids.write({"status": "accept"})
        work_acceptance.button_accept()
        self.assertEqual(work_acceptance.state, "accept")
