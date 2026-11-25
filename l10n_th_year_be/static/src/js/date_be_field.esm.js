/** @odoo-module **/

import {onMounted, onPatched, onWillUnmount, useRef} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {parseDate, parseDateTime} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {DateTimePicker} from "@web/core/datetime/datetime_picker";
import {DateTimePickerPopover} from "@web/core/datetime/datetime_picker_popover";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";
import {
    DateTimeField,
    dateField,
    dateRangeField,
    dateTimeField,
} from "@web/views/fields/datetime/datetime_field";
import {
    listDateField,
    listDateRangeField,
    listDateTimeField,
} from "@web/views/fields/datetime/list_datetime_field";
import {ListRenderer} from "@web/views/list/list_renderer";

const BUDDHIST_ERA_OFFSET = 543;
const AUTO_CONVERT_HALF_OFFSET = "half_offset";
const AUTO_CONVERT_100_YEARS = "100_years";
const AUTO_CONVERT_200_YEARS = "200_years";
const YEAR_FORMAT_OPTION = {
    label: _t("Year format"),
    name: "year_format",
    type: "selection",
    choices: [
        {label: _t("User/System Default"), value: "system"},
        {label: _t("Common Era (CE)"), value: "ce"},
        {label: _t("Buddhist Era (BE)"), value: "be"},
    ],
    help: _t("Choose the year display for this field."),
};

function getEffectiveYearFormat(options = {}, field = {}) {
    if (options.year_format === "be") {
        return "be";
    }
    if (options.year_format === "ce") {
        return "ce";
    }
    if (field.year_format === "be") {
        return "be";
    }
    if (field.year_format === "ce") {
        return "ce";
    }
    return session.l10n_th_date_year_format;
}

function isBuddhistEra(options = {}, field = {}) {
    return getEffectiveYearFormat(options, field) === "be";
}

function getBuddhistEraFromInput(input) {
    return input?.dataset.buddhistEra === "1";
}

function formatBuddhistEraYear(formattedValue, value) {
    if (!formattedValue || !value) {
        return formattedValue;
    }
    return formattedValue.replace(
        String(value.year),
        String(value.year + BUDDHIST_ERA_OFFSET)
    );
}

function getAutoConvertThreshold(strategy, currentYear = new Date().getFullYear()) {
    if (strategy === AUTO_CONVERT_HALF_OFFSET) {
        return currentYear + Math.floor(BUDDHIST_ERA_OFFSET / 2);
    }
    if (strategy === AUTO_CONVERT_100_YEARS) {
        return currentYear + 100;
    }
    if (strategy === AUTO_CONVERT_200_YEARS) {
        return currentYear + 200;
    }
    return currentYear + 100;
}

function autoConvertBuddhistEraInputYear(
    formattedValue,
    strategy = AUTO_CONVERT_100_YEARS,
    currentYear = new Date().getFullYear()
) {
    if (!formattedValue) {
        return formattedValue;
    }
    const threshold = getAutoConvertThreshold(strategy, currentYear);
    const currentBuddhistEraYear = currentYear + BUDDHIST_ERA_OFFSET;
    return formattedValue.replace(/\b\d{4}\b/g, (year) => {
        const yearNumber = Number(year);
        return yearNumber > threshold && yearNumber <= currentBuddhistEraYear
            ? String(yearNumber - BUDDHIST_ERA_OFFSET)
            : year;
    });
}

function normalizeInputYear(
    formattedValue,
    _buddhistEra,
    strategy = AUTO_CONVERT_100_YEARS,
    currentYear = new Date().getFullYear()
) {
    return autoConvertBuddhistEraInputYear(formattedValue, strategy, currentYear);
}

function getInputValueIndex(input) {
    return input.dataset.fieldRole === "end" ? 1 : 0;
}

function hasYearFormatOption(pickerProps = {}) {
    return Object.prototype.hasOwnProperty.call(pickerProps, "buddhistEra");
}

function parseNormalizedInput(input, pickerProps, hookParams) {
    const normalizedValue = normalizeInputYear(
        input.value,
        getBuddhistEraFromInput(input) || pickerProps.buddhistEra,
        session.l10n_th_date_auto_convert_be_input || AUTO_CONVERT_100_YEARS
    );
    input.value = normalizedValue;
    const parser = pickerProps.type === "datetime" ? parseDateTime : parseDate;
    return parser(normalizedValue, {
        tz: pickerProps.tz,
        format: hookParams.format,
    });
}

function getNormalizedPickerValue(getInputs, pickerProps, hookParams) {
    const inputs = getInputs();
    const currentValues = Array.isArray(pickerProps.value)
        ? pickerProps.value
        : [pickerProps.value];
    const values = currentValues.map((currentValue, index) => {
        const input = inputs[index];
        if (!input || !input.value) {
            return currentValue;
        }
        try {
            return parseNormalizedInput(input, pickerProps, hookParams);
        } catch {
            return currentValue;
        }
    });
    return values.length === 2 ? values : values[0];
}

function addBuddhistEraOption(fieldDefinition) {
    if (
        !fieldDefinition.supportedOptions.some(
            (option) => option.name === "year_format"
        )
    ) {
        fieldDefinition.supportedOptions.push(YEAR_FORMAT_OPTION);
    }

    const originalExtractProps = fieldDefinition.extractProps;
    fieldDefinition.extractProps = (params, dynamicInfo) => ({
        ...originalExtractProps(params, dynamicInfo),
        buddhistEra: isBuddhistEra(params.options),
        yearFormat: params.options.year_format,
    });
}

DateTimeField.props = {
    ...DateTimeField.props,
    buddhistEra: {type: Boolean, optional: true},
    yearFormat: {type: String, optional: true},
};

DateTimePicker.props = {
    ...DateTimePicker.props,
    buddhistEra: {type: Boolean, optional: true},
};
DateTimePickerPopover.props = {
    ...DateTimePickerPopover.props,
    pickerProps: {
        ...DateTimePickerPopover.props.pickerProps,
        shape: {
            ...DateTimePickerPopover.props.pickerProps.shape,
            buddhistEra: {type: Boolean, optional: true},
        },
    },
};

const datetimePickerService = registry.category("services").get("datetime_picker");

patch(datetimePickerService, {
    start(env, deps) {
        const service = super.start(env, deps);
        return {
            ...service,
            create(hookParams, getInputs) {
                let picker = null;
                const originalOnApply = hookParams.onApply;
                hookParams.onApply = async (...args) => {
                    if (picker) {
                        picker.state.buddhistEra = getBuddhistEraFromInput(
                            getInputs()[0]
                        );
                    }
                    if (picker && hasYearFormatOption(picker.state)) {
                        picker.state.value = getNormalizedPickerValue(
                            getInputs,
                            picker.state,
                            hookParams
                        );
                    }
                    return originalOnApply?.(...args);
                };
                picker = service.create(hookParams, getInputs);
                return {
                    ...picker,
                    open(inputIndex = 0) {
                        picker.state.buddhistEra = getBuddhistEraFromInput(
                            getInputs()[inputIndex]
                        );
                        return picker.open(inputIndex);
                    },
                };
            },
        };
    },
});

patch(DateTimeField.prototype, {
    setup() {
        super.setup();
        this.state.buddhistEra = this.props.buddhistEra;
        this.buddhistEraRoot = useRef("root");
        this.buddhistEraStartDate = useRef("start-date");
        this.buddhistEraEndDate = useRef("end-date");
        this.buddhistEraInputListeners = [];

        onMounted(() => {
            this.setupBuddhistEraInputs();
            this.updateBuddhistEraInputs();
        });
        onPatched(() => {
            this.setupBuddhistEraInputs();
            this.updateBuddhistEraInputs();
        });
        onWillUnmount(() => this.removeBuddhistEraInputListeners());
    },

    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        const formattedValue = super.getFormattedValue(valueIndex);

        if (!this.isBuddhistEraValue(valueIndex)) {
            return formattedValue;
        }
        return formatBuddhistEraYear(formattedValue, value);
    },

    getCommonEraFormattedValue(valueIndex) {
        return super.getFormattedValue(valueIndex);
    },

    getFieldYearFormat(valueIndex) {
        const fieldName = valueIndex ? this.endDateField : this.startDateField;
        return this.props.record.fields[fieldName]?.year_format;
    },

    isBuddhistEraValue(valueIndex) {
        return isBuddhistEra(
            {year_format: this.props.yearFormat},
            {year_format: this.getFieldYearFormat(valueIndex)}
        );
    },

    setupBuddhistEraInputs() {
        if (!this.buddhistEraRoot.el) {
            return;
        }
        const inputs = [
            this.buddhistEraStartDate.el,
            this.buddhistEraEndDate.el,
        ].filter(Boolean);

        for (const input of inputs) {
            if (input.dataset.buddhistEraListener) {
                continue;
            }
            input.dataset.buddhistEraListener = "1";
            input.dataset.fieldRole =
                input === this.buddhistEraEndDate.el ? "end" : "start";
            input.dataset.buddhistEra = this.isBuddhistEraValue(
                getInputValueIndex(input)
            )
                ? "1"
                : "0";

            const normalizeInput = () => {
                this.normalizeBuddhistEraInput(input);
            };
            const onNormalize = () => {
                normalizeInput();
            };
            const onCommitKeydown = (ev) => {
                if (ev.key === "Enter" || ev.key === "Tab") {
                    normalizeInput();
                }
            };
            const onRefresh = () => setTimeout(() => this.updateBuddhistEraInputs());

            input.addEventListener("change", onNormalize, true);
            input.addEventListener("blur", onNormalize, true);
            input.addEventListener("focusout", onNormalize, true);
            input.addEventListener("keydown", onCommitKeydown, true);
            input.addEventListener("click", onRefresh);
            input.addEventListener("focus", onRefresh);
            this.buddhistEraInputListeners.push([input, "change", onNormalize, true]);
            this.buddhistEraInputListeners.push([input, "blur", onNormalize, true]);
            this.buddhistEraInputListeners.push([input, "focusout", onNormalize, true]);
            this.buddhistEraInputListeners.push([
                input,
                "keydown",
                onCommitKeydown,
                true,
            ]);
            this.buddhistEraInputListeners.push([input, "click", onRefresh, false]);
            this.buddhistEraInputListeners.push([input, "focus", onRefresh, false]);
        }
    },

    removeBuddhistEraInputListeners() {
        for (const [input, eventName, listener, useCapture] of this
            .buddhistEraInputListeners) {
            input.removeEventListener(eventName, listener, useCapture);
            delete input.dataset.buddhistEraListener;
        }
        this.buddhistEraInputListeners = [];
    },

    normalizeBuddhistEraInput(input) {
        input.value = normalizeInputYear(
            input.value,
            getBuddhistEraFromInput(input),
            session.l10n_th_date_auto_convert_be_input || AUTO_CONVERT_100_YEARS
        );
    },

    updateBuddhistEraInputs() {
        if (!this.buddhistEraRoot.el) {
            return;
        }
        const inputs = [
            this.buddhistEraStartDate.el,
            this.buddhistEraEndDate.el,
        ].filter(Boolean);
        inputs.forEach((input) => {
            const index = getInputValueIndex(input);
            input.dataset.buddhistEra = this.isBuddhistEraValue(index) ? "1" : "0";
            if (!getBuddhistEraFromInput(input)) {
                return;
            }
            const buddhistEraValue = this.getFormattedValue(index);
            const commonEraValue = this.getCommonEraFormattedValue(index);
            if (
                !input.value ||
                input.value === commonEraValue ||
                document.activeElement !== input
            ) {
                input.value = buddhistEraValue;
            }
        });
    },
});

patch(DateTimePicker.prototype, {
    onWillRender() {
        super.onWillRender();

        if (!this.props.buddhistEra) {
            return;
        }
        this.title = this.formatBuddhistEraPickerText(this.title);
        this.items = this.formatBuddhistEraPickerItems(this.items);
    },

    formatBuddhistEraPickerText(text) {
        if (Array.isArray(text)) {
            return text.map((value) => this.formatBuddhistEraPickerText(value));
        }
        return String(text).replace(/\b\d{4}\b/g, (year) =>
            String(Number(year) + BUDDHIST_ERA_OFFSET)
        );
    },

    formatBuddhistEraPickerItems(items) {
        return items.map((item) => {
            if (item.weeks) {
                return item;
            }
            return {
                ...item,
                label: this.formatBuddhistEraPickerText(item.label),
            };
        });
    },
});

patch(ListRenderer.prototype, {
    getFormattedValue(column, record) {
        const formattedValue = super.getFormattedValue(column, record);

        if (
            !isBuddhistEra(column.options, record.fields[column.name]) ||
            !["date", "datetime"].includes(record.fields[column.name]?.type)
        ) {
            return formattedValue;
        }
        return formatBuddhistEraYear(formattedValue, record.data[column.name]);
    },
});

addBuddhistEraOption(dateField);
addBuddhistEraOption(dateTimeField);
addBuddhistEraOption(dateRangeField);
addBuddhistEraOption(listDateField);
addBuddhistEraOption(listDateTimeField);
addBuddhistEraOption(listDateRangeField);
