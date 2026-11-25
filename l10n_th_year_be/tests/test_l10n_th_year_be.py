import json
import shutil
import subprocess
import unittest
from contextlib import contextmanager
from datetime import date, datetime
from unittest.mock import Mock

from odoo import fields
from odoo.http import _request_stack, get_default_session
from odoo.modules.module import get_manifest
from odoo.tests.common import TransactionCase
from odoo.tools import DotDict
from odoo.tools.misc import file_path

from odoo.addons.l10n_th_year_be.models.res_users import (
    AUTO_CONVERT_100_YEARS,
    AUTO_CONVERT_200_YEARS,
    AUTO_CONVERT_HALF_OFFSET,
    AUTO_CONVERT_PARAM,
    YEAR_FORMAT_BE,
    YEAR_FORMAT_CE,
    YEAR_FORMAT_PARAM,
    YEAR_FORMAT_SYSTEM,
    format_buddhist_era_year,
)


class TestL10nThYearBe(TransactionCase):
    @contextmanager
    def _mock_request_context(self, cookies=None):
        session = DotDict(get_default_session())
        session.uid = self.env.uid
        session.context = dict(self.env["res.users"].context_get())
        session.debug = ""
        session.profile_session = False
        session.profile_collectors = {}
        session.profile_params = {}
        request = Mock(
            httprequest=Mock(
                host="localhost",
                cookies=cookies or {},
                user_agent=Mock(string="odoo-test"),
            ),
            cookies=cookies or {},
            db=self.env.cr.dbname,
            registry=self.env.registry,
            env=self.env,
            session=session,
        )
        try:
            self.env.flush_all()
            self.env.invalidate_all()
            _request_stack.push(request)
            yield request
            self.env.flush_all()
            self.env.invalidate_all()
        finally:
            _request_stack.pop()

    @staticmethod
    def _run_js_helpers(script_body):
        node = shutil.which("node")
        if not node:
            raise unittest.SkipTest(
                "Node.js is required to execute client utility tests."
            )

        asset_path = file_path("l10n_th_year_be/static/src/js/date_be_field.esm.js")
        with open(asset_path, encoding="utf-8") as asset_file:
            asset_content = asset_file.read()
        helper_start = asset_content.index("function formatBuddhistEraYear")
        helper_end = asset_content.index("function addBuddhistEraOption")
        helpers = (
            "const BUDDHIST_ERA_OFFSET = 543;\n"
            'const AUTO_CONVERT_HALF_OFFSET = "half_offset";\n'
            'const AUTO_CONVERT_100_YEARS = "100_years";\n'
            'const AUTO_CONVERT_200_YEARS = "200_years";\n'
            + asset_content[helper_start:helper_end]
        )
        script = f"eval({json.dumps(helpers + script_body)});"
        return subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_backend_asset_is_declared(self):
        manifest = get_manifest("l10n_th_year_be")

        self.assertIn(
            "l10n_th_year_be/static/src/js/date_be_field.esm.js",
            manifest["assets"]["web.assets_backend"],
        )
        self.assertNotIn(
            "l10n_th_year_be/static/src/js/date_be_utils.js",
            manifest["assets"]["web.assets_backend"],
        )

    def test_manual_input_year_normalization_matrix(self):
        matrix_script = """
            const strategy = AUTO_CONVERT_100_YEARS;
            const currentYear = 2026;
            const cases = [
                [
                    "BE display, user enters CE date year",
                    normalizeInputYear(
                        "08/02/2026", true, strategy, currentYear
                    ),
                    "08/02/2026",
                ],
                [
                    "BE display, user enters BE date year",
                    normalizeInputYear(
                        "08/02/2569", true, strategy, currentYear
                    ),
                    "08/02/2026",
                ],
                [
                    "CE display, user enters BE date year",
                    normalizeInputYear(
                        "08/02/2569", false, strategy, currentYear
                    ),
                    "08/02/2026",
                ],
                [
                    "CE display, user enters year just after current BE",
                    normalizeInputYear(
                        "08/02/2570", false, strategy, currentYear
                    ),
                    "08/02/2570",
                ],
                [
                    "BE display, user enters year after current BE",
                    normalizeInputYear(
                        "08/02/3112", true, strategy, currentYear
                    ),
                    "08/02/3112",
                ],
                [
                    "CE display, user enters year after current BE",
                    normalizeInputYear(
                        "08/02/3112", false, strategy, currentYear
                    ),
                    "08/02/3112",
                ],
                [
                    "BE display, user enters CE datetime year",
                    normalizeInputYear(
                        "08/02/2026 14:30:00", true, strategy, currentYear
                    ),
                    "08/02/2026 14:30:00",
                ],
                [
                    "BE display, user enters BE datetime year",
                    normalizeInputYear(
                        "08/02/2569 14:30:00", true, strategy, currentYear
                    ),
                    "08/02/2026 14:30:00",
                ],
                [
                    "CE display, user enters BE datetime year",
                    normalizeInputYear(
                        "08/02/2569 14:30:00", false, strategy, currentYear
                    ),
                    "08/02/2026 14:30:00",
                ],
            ];
            process.stdout.write(JSON.stringify(cases));
        """
        result = self._run_js_helpers(matrix_script)

        for label, actual, expected in json.loads(result.stdout):
            with self.subTest(label=label):
                self.assertEqual(actual, expected)

    def test_manual_input_year_normalization_boundary_analysis(self):
        boundary_script = """
            const currentYear = 2026;
            const currentBE = currentYear + BUDDHIST_ERA_OFFSET;
            const strategies = [
                [
                    AUTO_CONVERT_HALF_OFFSET,
                    currentYear + Math.floor(BUDDHIST_ERA_OFFSET / 2),
                ],
                [AUTO_CONVERT_100_YEARS, currentYear + 100],
                [AUTO_CONVERT_200_YEARS, currentYear + 200],
            ];
            const cases = [];
            for (const [strategy, threshold] of strategies) {
                cases.push([
                    `${strategy}: empty input`,
                    normalizeInputYear("", false, strategy, currentYear),
                    "",
                ]);
                cases.push([
                    `${strategy}: threshold is not converted`,
                    normalizeInputYear(
                        `03/07/${threshold}`,
                        false,
                        strategy,
                        currentYear
                    ),
                    `03/07/${threshold}`,
                ]);
                cases.push([
                    `${strategy}: threshold plus one is converted`,
                    normalizeInputYear(
                        `03/07/${threshold + 1}`,
                        false,
                        strategy,
                        currentYear
                    ),
                    `03/07/${threshold + 1 - BUDDHIST_ERA_OFFSET}`,
                ]);
                cases.push([
                    `${strategy}: current BE is converted`,
                    normalizeInputYear(
                        `03/07/${currentBE}`,
                        false,
                        strategy,
                        currentYear
                    ),
                    `03/07/${currentYear}`,
                ]);
                cases.push([
                    `${strategy}: current BE plus one is not converted`,
                    normalizeInputYear(
                        `03/07/${currentBE + 1}`,
                        false,
                        strategy,
                        currentYear
                    ),
                    `03/07/${currentBE + 1}`,
                ]);
                cases.push([
                    `${strategy}: datetime threshold plus one is converted`,
                    normalizeInputYear(
                        `03/07/${threshold + 1} 09:45:30`,
                        true,
                        strategy,
                        currentYear
                    ),
                    `03/07/${threshold + 1 - BUDDHIST_ERA_OFFSET} 09:45:30`,
                ]);
            }
            process.stdout.write(JSON.stringify(cases));
        """
        result = self._run_js_helpers(boundary_script)

        for label, actual, expected in json.loads(result.stdout):
            with self.subTest(label=label):
                self.assertEqual(actual, expected)

    def test_date_time_picker_popover_accepts_buddhist_era_prop(self):
        asset_path = file_path("l10n_th_year_be/static/src/js/date_be_field.esm.js")
        with open(asset_path, encoding="utf-8") as asset_file:
            asset_content = asset_file.read()

        self.assertIn("DateTimePickerPopover", asset_content)
        self.assertIn("DateTimePickerPopover.props", asset_content)
        self.assertIn("pickerProps", asset_content)
        self.assertIn("buddhistEra: {type: Boolean, optional: true}", asset_content)

    def test_editable_date_inputs_are_formatted_and_parsed_as_buddhist_era(self):
        asset_path = file_path("l10n_th_year_be/static/src/js/date_be_field.esm.js")
        with open(asset_path, encoding="utf-8") as asset_file:
            asset_content = asset_file.read()

        self.assertIn("normalizeInputYear", asset_content)
        self.assertIn("session.l10n_th_date_auto_convert_be_input", asset_content)
        self.assertIn("autoConvertBuddhistEraInputYear", asset_content)
        self.assertIn("function getEffectiveYearFormat", asset_content)
        self.assertIn('field.year_format === "be"', asset_content)
        self.assertIn('field.year_format === "ce"', asset_content)
        self.assertIn("yearFormat: params.options.year_format", asset_content)
        self.assertIn("getFieldYearFormat", asset_content)
        self.assertIn("isBuddhistEraValue", asset_content)
        self.assertIn("getBuddhistEraFromInput", asset_content)
        self.assertIn(
            "isBuddhistEra(column.options, record.fields[column.name])", asset_content
        )
        self.assertIn(
            'registry.category("services").get("datetime_picker")', asset_content
        )
        self.assertIn("getNormalizedPickerValue", asset_content)
        self.assertIn("parseNormalizedInput", asset_content)
        self.assertIn("picker.state.value = getNormalizedPickerValue", asset_content)
        self.assertIn(
            'pickerProps.type === "datetime" ? parseDateTime : parseDate', asset_content
        )
        self.assertIn(
            "yearNumber > threshold && yearNumber <= currentBuddhistEraYear",
            asset_content,
        )
        self.assertNotIn("formatCommonEraInputYear", asset_content)
        self.assertIn("getAutoConvertThreshold", asset_content)
        self.assertIn("AUTO_CONVERT_HALF_OFFSET", asset_content)
        self.assertIn("AUTO_CONVERT_100_YEARS", asset_content)
        self.assertIn("AUTO_CONVERT_200_YEARS", asset_content)
        self.assertIn("updateBuddhistEraInputs", asset_content)
        self.assertIn('useRef("start-date")', asset_content)
        self.assertIn('useRef("end-date")', asset_content)
        self.assertNotIn('querySelectorAll("input[data-field]")', asset_content)
        self.assertNotIn('input.addEventListener("input"', asset_content)
        self.assertIn(
            'input.addEventListener("change", onNormalize, true)', asset_content
        )
        self.assertIn(
            'input.addEventListener("blur", onNormalize, true)', asset_content
        )
        self.assertIn(
            'input.addEventListener("focusout", onNormalize, true)', asset_content
        )
        self.assertIn(
            'input.addEventListener("keydown", onCommitKeydown, true)', asset_content
        )
        self.assertIn('ev.key === "Enter" || ev.key === "Tab"', asset_content)
        self.assertNotIn(
            (
                "normalizeInput();\n"
                "        setTimeout(() => this.updateBuddhistEraInputs());"
            ),
            asset_content,
        )
        self.assertNotIn('addEventListener("pointerdown"', asset_content)
        self.assertNotIn("buddhistEraDocumentListeners", asset_content)
        self.assertNotIn('classList.contains("text-primary")', asset_content)
        self.assertIn(
            'this.buddhistEraInputListeners.push([input, "change", onNormalize, true])',
            asset_content,
        )

    def test_module_views_are_declared(self):
        self.env.ref("l10n_th_year_be.res_config_settings_view_form")
        self.env.ref("l10n_th_year_be.view_users_form")
        self.env.ref("l10n_th_year_be.view_users_form_simple_modif")

    def test_settings_view_uses_regional_formats_block_in_languages_area(self):
        view = self.env.ref("l10n_th_year_be.res_config_settings_view_form")

        self.assertIn("Regional Formats", view.arch_db)
        self.assertIn("l10n_th_regional_formats_setting_container", view.arch_db)
        self.assertIn("languages_setting_container", view.arch_db)
        self.assertNotIn("product_general_settings", view.arch_db)

    def test_user_preference_field_is_self_accessible(self):
        self.assertIn("l10n_th_date_year_format", self.env.user.SELF_READABLE_FIELDS)
        self.assertIn("l10n_th_date_year_format", self.env.user.SELF_WRITEABLE_FIELDS)

    def test_session_info_exposes_year_format_and_auto_convert_setting(self):
        self.env["ir.config_parameter"].sudo().set_param(
            YEAR_FORMAT_PARAM, YEAR_FORMAT_BE
        )
        self.env["ir.config_parameter"].sudo().set_param(
            AUTO_CONVERT_PARAM, AUTO_CONVERT_100_YEARS
        )
        self.env.user.l10n_th_date_year_format = YEAR_FORMAT_SYSTEM

        session_info = self.env["ir.http"]._get_l10n_th_year_be_session_info()

        self.assertEqual(session_info["l10n_th_date_year_format"], YEAR_FORMAT_BE)
        self.assertEqual(
            session_info["l10n_th_date_auto_convert_be_input"],
            AUTO_CONVERT_100_YEARS,
        )

    def test_auto_convert_setting_defaults_to_100_year_detection(self):
        settings = self.env["res.config.settings"].create({})

        self.assertEqual(
            settings.l10n_th_date_auto_convert_be_input, AUTO_CONVERT_100_YEARS
        )

    def test_legacy_disabled_auto_convert_param_is_sanitized(self):
        self.env["ir.config_parameter"].sudo().set_param(AUTO_CONVERT_PARAM, "disabled")

        settings = self.env["res.config.settings"].create({})
        session_info = self.env["ir.http"]._get_l10n_th_year_be_session_info()

        self.assertEqual(
            settings.l10n_th_date_auto_convert_be_input, AUTO_CONVERT_100_YEARS
        )
        self.assertEqual(
            session_info["l10n_th_date_auto_convert_be_input"],
            AUTO_CONVERT_100_YEARS,
        )

    def test_auto_convert_algorithms_are_available(self):
        field = self.env["res.config.settings"]._fields[
            "l10n_th_date_auto_convert_be_input"
        ]

        self.assertEqual(
            {choice for choice, _label in field.selection},
            {
                AUTO_CONVERT_HALF_OFFSET,
                AUTO_CONVERT_100_YEARS,
                AUTO_CONVERT_200_YEARS,
            },
        )
        self.assertEqual(
            dict(field.selection)[AUTO_CONVERT_100_YEARS],
            "100 years",
        )

    def test_python_field_year_format_is_exposed_in_field_description(self):
        date_field = fields.Date(year_format=YEAR_FORMAT_BE)
        datetime_field = fields.Datetime(year_format=YEAR_FORMAT_CE)

        self.assertEqual(
            date_field.get_description(self.env, attributes=["year_format"])[
                "year_format"
            ],
            YEAR_FORMAT_BE,
        )
        self.assertEqual(
            datetime_field.get_description(self.env, attributes=["year_format"])[
                "year_format"
            ],
            YEAR_FORMAT_CE,
        )

    def test_invalid_python_field_year_format_is_not_exposed(self):
        invalid_date_field = fields.Date(year_format="invalid")
        description = invalid_date_field.get_description(
            self.env, attributes=["year_format"]
        )

        self.assertNotIn("year_format", description)

    def test_year_format_description_handles_missing_field_args(self):
        date_field = fields.Date(year_format=YEAR_FORMAT_BE)
        date_field._args__ = None

        description = date_field.get_description(self.env, attributes=["year_format"])

        self.assertNotIn("year_format", description)

    def test_base_model_fields_get_handles_datetime_description(self):
        description = self.env["res.users"].fields_get(
            ["create_date", "write_date"], attributes=["type", "year_format"]
        )

        self.assertEqual(description["create_date"]["type"], "datetime")
        self.assertEqual(description["write_date"]["type"], "datetime")

    def test_format_buddhist_era_year_handles_empty_values(self):
        self.assertEqual(format_buddhist_era_year("", None), "")
        self.assertEqual(format_buddhist_era_year("07/03/2026", None), "07/03/2026")
        self.assertEqual(
            format_buddhist_era_year("07/03/2026", date(2026, 7, 3)),
            "07/03/2569",
        )

    def test_user_setting_overrides_system_setting_for_all_choices(self):
        expected_by_choice = {
            YEAR_FORMAT_SYSTEM: {
                YEAR_FORMAT_CE: YEAR_FORMAT_CE,
                YEAR_FORMAT_BE: YEAR_FORMAT_BE,
            },
            YEAR_FORMAT_CE: {
                YEAR_FORMAT_CE: YEAR_FORMAT_CE,
                YEAR_FORMAT_BE: YEAR_FORMAT_CE,
            },
            YEAR_FORMAT_BE: {
                YEAR_FORMAT_CE: YEAR_FORMAT_BE,
                YEAR_FORMAT_BE: YEAR_FORMAT_BE,
            },
        }

        for user_choice, expected_by_system_choice in expected_by_choice.items():
            for system_choice, expected in expected_by_system_choice.items():
                with self.subTest(user_choice=user_choice, system_choice=system_choice):
                    self.env["ir.config_parameter"].sudo().set_param(
                        YEAR_FORMAT_PARAM, system_choice
                    )
                    self.env.user.l10n_th_date_year_format = user_choice

                    self.assertEqual(
                        self.env.user._get_l10n_th_effective_date_year_format(),
                        expected,
                    )

    def test_field_setting_overrides_user_and_system_settings_for_all_choices(self):
        field_choices = [
            ("unset", None),
            ("year_format_system", YEAR_FORMAT_SYSTEM),
            ("year_format_ce", YEAR_FORMAT_CE),
            ("year_format_be", YEAR_FORMAT_BE),
        ]
        user_choices = [YEAR_FORMAT_SYSTEM, YEAR_FORMAT_CE, YEAR_FORMAT_BE]
        system_choices = [YEAR_FORMAT_CE, YEAR_FORMAT_BE]

        for field_label, field_year_format in field_choices:
            for user_choice in user_choices:
                for system_choice in system_choices:
                    with self.subTest(
                        field_choice=field_label,
                        user_choice=user_choice,
                        system_choice=system_choice,
                    ):
                        self.env["ir.config_parameter"].sudo().set_param(
                            YEAR_FORMAT_PARAM, system_choice
                        )
                        self.env.user.l10n_th_date_year_format = user_choice

                        if field_year_format in (YEAR_FORMAT_CE, YEAR_FORMAT_BE):
                            expected = field_year_format
                        elif user_choice == YEAR_FORMAT_SYSTEM:
                            expected = system_choice
                        else:
                            expected = user_choice

                        self.assertEqual(
                            self.env.user._get_l10n_th_effective_date_year_format(
                                field_year_format=field_year_format,
                            ),
                            expected,
                        )

    def test_element_setting_overrides_field_user_and_system_settings_for_all_choices(
        self,
    ):
        element_choices = [
            ("unset", None),
            ("year_format_system", YEAR_FORMAT_SYSTEM),
            ("year_format_ce", YEAR_FORMAT_CE),
            ("year_format_be", YEAR_FORMAT_BE),
        ]
        field_choices = [
            ("unset", None),
            ("year_format_system", YEAR_FORMAT_SYSTEM),
            ("year_format_ce", YEAR_FORMAT_CE),
            ("year_format_be", YEAR_FORMAT_BE),
        ]
        user_choices = [YEAR_FORMAT_SYSTEM, YEAR_FORMAT_CE, YEAR_FORMAT_BE]
        system_choices = [YEAR_FORMAT_CE, YEAR_FORMAT_BE]

        for element_label, element_year_format in element_choices:
            for field_label, field_year_format in field_choices:
                for user_choice in user_choices:
                    for system_choice in system_choices:
                        with self.subTest(
                            element_choice=element_label,
                            field_choice=field_label,
                            user_choice=user_choice,
                            system_choice=system_choice,
                        ):
                            self.env["ir.config_parameter"].sudo().set_param(
                                YEAR_FORMAT_PARAM, system_choice
                            )
                            self.env.user.l10n_th_date_year_format = user_choice

                            if element_year_format in (YEAR_FORMAT_CE, YEAR_FORMAT_BE):
                                expected = element_year_format
                            elif field_year_format in (YEAR_FORMAT_CE, YEAR_FORMAT_BE):
                                expected = field_year_format
                            elif user_choice == YEAR_FORMAT_SYSTEM:
                                expected = system_choice
                            else:
                                expected = user_choice

                            self.assertEqual(
                                self.env.user._get_l10n_th_effective_date_year_format(
                                    element_year_format=element_year_format,
                                    field_year_format=field_year_format,
                                ),
                                expected,
                            )

    def test_qweb_date_converter_uses_effective_year_format(self):
        converter = self.env["ir.qweb.field.date"]
        value = datetime(2026, 7, 3).date()

        self.env["ir.config_parameter"].sudo().set_param(
            YEAR_FORMAT_PARAM, YEAR_FORMAT_BE
        )
        self.env.user.l10n_th_date_year_format = YEAR_FORMAT_SYSTEM

        self.assertIn("2569", converter.value_to_html(value, {}))
        self.assertIn(
            "2026", converter.value_to_html(value, {"year_format": YEAR_FORMAT_CE})
        )
        self.assertIn(
            "2569", converter.value_to_html(value, {"year_format": YEAR_FORMAT_BE})
        )

    def test_qweb_date_converter_handles_string_value_and_available_options(self):
        converter = self.env["ir.qweb.field.date"]
        options = converter.get_available_options()

        self.assertIn("year_format", options)
        self.assertEqual(options["year_format"]["string"], "Year format")
        self.assertIn(
            "2569",
            converter.value_to_html("2026-07-03", {"year_format": YEAR_FORMAT_BE}),
        )

    def test_qweb_datetime_converter_uses_effective_year_format(self):
        converter = self.env["ir.qweb.field.datetime"]
        value = datetime(2026, 7, 3, 6, 30, 15)

        self.env["ir.config_parameter"].sudo().set_param(
            YEAR_FORMAT_PARAM, YEAR_FORMAT_CE
        )
        self.env.user.l10n_th_date_year_format = YEAR_FORMAT_BE

        self.assertIn("2569", converter.value_to_html(value, {}))
        self.assertIn(
            "2026", converter.value_to_html(value, {"year_format": YEAR_FORMAT_CE})
        )
        self.assertIn(
            "2569", converter.value_to_html(value, {"year_format": YEAR_FORMAT_BE})
        )

    def test_qweb_datetime_converter_handles_string_value_tz_and_available_options(
        self,
    ):
        converter = self.env["ir.qweb.field.datetime"]
        options = converter.get_available_options()

        self.assertIn("year_format", options)
        self.assertEqual(options["year_format"]["string"], "Year format")
        self.assertIn(
            "2569",
            converter.value_to_html(
                "2026-07-03 06:30:15",
                {"year_format": YEAR_FORMAT_BE, "tz_name": "Asia/Bangkok"},
            ),
        )

    def test_session_info_includes_year_be_payload(self):
        self.env["ir.config_parameter"].sudo().set_param(
            YEAR_FORMAT_PARAM, YEAR_FORMAT_BE
        )
        self.env["ir.config_parameter"].sudo().set_param(
            AUTO_CONVERT_PARAM, AUTO_CONVERT_100_YEARS
        )
        self.env.user.l10n_th_date_year_format = YEAR_FORMAT_SYSTEM

        with self._mock_request_context(
            cookies={"cids": str(self.env.user.company_id.id)}
        ):
            session_info = self.env["ir.http"].session_info()

        self.assertEqual(session_info["uid"], self.env.uid)
        self.assertEqual(session_info["l10n_th_date_year_format"], YEAR_FORMAT_BE)
        self.assertEqual(
            session_info["l10n_th_date_auto_convert_be_input"],
            AUTO_CONVERT_100_YEARS,
        )
