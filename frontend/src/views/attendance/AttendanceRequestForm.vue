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
				@validateForm="validateForm"
			/>
		</template>
	</AppShell>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"
import { useRoute } from "vue-router"

import AppShell from "@/components/AppShell.vue"
import FormView from "@/components/FormView.vue"

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

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Attendance Request" },
	auto: true,
	transform(data) {
		if (!attendanceRequest.value.reason) {
			for (const field of data) {
				if (["custom_hours_requested", "custom_limit_balance_html"].includes(field.fieldname)) {
					field.hidden = true
				}
			}
		}
		// shift is auto-derived server-side from the employee's active shift
		// assignment (hrms's Attendance Request.validate_shifts) — no need to
		// show or fill it here
		const shiftField = data.find((field) => field.fieldname === "shift")
		if (shiftField) shiftField.hidden = true

		if (props.id) return data
		return data.filter(
			(field) => !["employee", "employee_name", "status", "company"].includes(field.fieldname)
		)
	},
})

// form scripts
watch(
	() => attendanceRequest.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== employee.data.name) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
	}
)

watch(
	() => attendanceRequest.value.from_date,
	(from_date) => {
		if (!attendanceRequest.value.to_date) {
			attendanceRequest.value.to_date = from_date
		}
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
		const half_day_date = formFields.data.find((field) => field.fieldname === "half_day_date")
		half_day_date.hidden = !half_day
	}
)

watch(
	() => attendanceRequest.value.reason,
	(reason) => {
		const hoursField = formFields.data?.find(
			(field) => field.fieldname === "custom_hours_requested"
		)
		const limitBalanceField = formFields.data?.find(
			(field) => field.fieldname === "custom_limit_balance_html"
		)
		if (!hoursField && !limitBalanceField) return

		if (!reason) {
			if (hoursField) hoursField.hidden = true
			if (limitBalanceField) limitBalanceField.hidden = true
			return
		}

		createResource({
			url: "craft_hr.api.get_attendance_request_type_hours_based",
			params: { reason },
			onSuccess(isHoursBased) {
				if (hoursField) hoursField.hidden = !isHoursBased
				if (limitBalanceField) limitBalanceField.hidden = !isHoursBased
			},
		}).reload()
	}
)

// helper functions
function setFormReadOnly() {
	formFields.data.map((field) => (field.read_only = true))
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) return

	const error_message = from_date > to_date ? __("To Date cannot be before From Date") : ""

	const from_date_field = formFields.data.find((field) => field.fieldname === "from_date")
	from_date_field.error_message = error_message
}

function validateForm() {
	attendanceRequest.value.employee = employee.data.name
}
</script>
