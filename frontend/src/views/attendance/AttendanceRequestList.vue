<template>
	<AppShell>
		<template #body>
			<ListView
				doctype="Attendance Request"
				:pageTitle="__('Attendance Request History')"
				:fields="ATTENDANCE_REQUEST_FIELDS"
				:filterConfig="FILTER_CONFIG"
			/>
		</template>
	</AppShell>
</template>

<script setup>
import AppShell from "@/components/AppShell.vue"
import ListView from "@/components/ListView.vue"
import { inject } from "vue"

const __ = inject("$translate")

const ATTENDANCE_REQUEST_FIELDS = ["name", "reason", "from_date", "to_date", "docstatus"]
const FILTER_CONFIG = [
	{
		fieldname: "shift",
		fieldtype: "Link",
		label: __("Shift"),
		options: "Shift Type",
	},
	{ fieldname: "from_date", fieldtype: "Date", label: __("From Date") },
	{ fieldname: "to_date", fieldtype: "Date", label: __("To Date") },
]
</script>
