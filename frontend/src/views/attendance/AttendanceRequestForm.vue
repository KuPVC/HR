<template>
	<AppShell :pageTitle="__('Attendance Request')">
		<template #body>
			<FormView
				v-if="formFields.data"
				doctype="Attendance Request"
				v-model="attendanceRequest"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				:showCommentsView="true"
				@validateForm="validateForm"
			>
				<template #custom_limit_balance_html>
					<AttendanceRequestLimitBalance
						:employee="attendanceRequest.employee || employee.data?.name"
						:reason="attendanceRequest.reason"
						:fromDate="attendanceRequest.from_date"
					/>
				</template>
			</FormView>
		</template>
	</AppShell>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"
import { useRoute } from "vue-router"

import AppShell from "@/components/AppShell.vue"
import FormView from "@/components/FormView.vue"
import AttendanceRequestLimitBalance from "@/components/AttendanceRequestLimitBalance.vue"
import { formatHoursDuration } from "@/utils/formatters"

const employee = inject("$employee")
const __ = inject("$translate")
const route = useRoute()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const attendanceRequest = ref({})

if (!props.id && route.query.date) {
	attendanceRequest.value.from_date = route.query.date
	attendanceRequest.value.to_date = route.query.date
}

// pre-fill the hours field when arriving from a short-hours day on the
// calendar - it stays hidden until the employee picks an hours-based
// Reason (see the reason watcher below), but the value is ready by then.
if (!props.id && route.query.hours) {
	attendanceRequest.value.custom_hours_requested = Number(route.query.hours)
}

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Attendance Request" },
	auto: true,
	transform(data) {
		if (!attendanceRequest.value.reason) {
			const hoursField = data.find(
				(field) => field.fieldname === "custom_hours_requested"
			)
			if (hoursField) hoursField.hidden = true
		}
		// shift is auto-derived server-side from the employee's active shift
		// assignment (hrms's Attendance Request.validate_shifts) — no need to
		// show or fill it here
		const shiftField = data.find((field) => field.fieldname === "shift")
		if (shiftField) shiftField.hidden = true

		// Employees only ever fill in one date - to_date is always kept in
		// sync with from_date (see the from_date watcher below), so it's
		// never shown as a separate field to fill in twice.
		const to_date_field = data.find((field) => field.fieldname === "to_date")
		if (to_date_field) to_date_field.hidden = true

		const hoursField = data.find(
			(field) => field.fieldname === "custom_hours_requested"
		)
		if (hoursField) {
			hoursField.description = __(
				"Enter the number of hours as a decimal - e.g. 0.5 for 30 minutes, 1.25 for 1 hr 15 min. Or use the clock button to enter hr/min/sec directly."
			)
			hoursField.valuePreview = (value) =>
				value ? __("Requested: {0}", [formatHoursDuration(Number(value))]) : ""
			hoursField.durationInput = true
		}

		if (props.id) return data
		return data.filter(
			(field) =>
				!["employee", "employee_name", "status", "company"].includes(
					field.fieldname
				)
		)
	},
})

// Backs refreshReasonFilter() below.
const relevantTypes = createResource({
	url: "sj_hr.overrides.attendance_request.get_relevant_request_types",
	auto: false,
})

// form scripts
watch(
	() => attendanceRequest.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== employee.data.name) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
		refreshReasonFilter()
	}
)

watch(
	() => attendanceRequest.value.from_date,
	(from_date) => {
		attendanceRequest.value.to_date = from_date
		refreshReasonFilter()
	}
)

watch(
	() => [attendanceRequest.value.from_date, attendanceRequest.value.to_date],
	([from_date, to_date]) => {
		validateDates(from_date, to_date)
	}
)

watch(
	() => attendanceRequest.value.half_day,
	(half_day) => {
		const half_day_date = formFields.data.find(
			(field) => field.fieldname === "half_day_date"
		)
		half_day_date.hidden = !half_day
	}
)

watch(
	() => attendanceRequest.value.reason,
	(reason) => {
		const hoursField = formFields.data?.find(
			(field) => field.fieldname === "custom_hours_requested"
		)
		if (!hoursField) return

		if (!reason) {
			hoursField.hidden = true
			return
		}

		createResource({
			url: "craft_hr.api.get_attendance_request_type_hours_based",
			params: { reason },
			onSuccess(isHoursBased) {
				hoursField.hidden = !isHoursBased
			},
		}).reload()
	}
)

// helper functions
function refreshReasonFilter() {
	// Narrow the Reason dropdown to only the Attendance Request Types that
	// actually match a real issue (late entry / early exit / missed punch /
	// short hours / absent) on this employee's attendance for the selected
	// date - avoids staff picking a type that's irrelevant to what's
	// actually wrong, purely because it was the first option they
	// recognized. Falls back to just active types when there isn't enough
	// context yet (no date picked, or no issue found for that date).
	const reason_field = formFields.data?.find((field) => field.fieldname === "reason")
	if (!reason_field) return

	const fallbackFilters = { is_active: 1 }
	if (!attendanceRequest.value.employee || !attendanceRequest.value.from_date) {
		reason_field.linkFilters = fallbackFilters
		return
	}

	relevantTypes.submit(
		{
			employee: attendanceRequest.value.employee,
			from_date: attendanceRequest.value.from_date,
			to_date: attendanceRequest.value.to_date || attendanceRequest.value.from_date,
		},
		{
			onSuccess(result) {
				reason_field.linkFilters =
					result && result.has_issue_data
						? { name: ["in", result.types], is_active: 1 }
						: fallbackFilters
			},
			onError() {
				reason_field.linkFilters = fallbackFilters
			},
		}
	)
}

function setFormReadOnly() {
	formFields.data.map((field) => (field.read_only = true))
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) return

	const error_message =
		from_date > to_date ? __("To Date cannot be before From Date") : ""

	const from_date_field = formFields.data.find(
		(field) => field.fieldname === "from_date"
	)
	from_date_field.error_message = error_message
}

function validateForm() {
	attendanceRequest.value.employee = employee.data.name
}
</script>
