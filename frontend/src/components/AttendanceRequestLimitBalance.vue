<template>
	<div
		v-if="tableRows.length"
		class="flex flex-col gap-2 rounded-lg border-l-4 border-blue-500 bg-gray-50 p-3"
	>
		<div class="text-xs font-semibold uppercase tracking-wide text-gray-500">
			{{ __("Limit Balance") }}
		</div>
		<table class="w-full text-xs">
			<thead>
				<tr class="text-gray-500">
					<th class="pb-1 text-left font-semibold">{{ __("Period") }}</th>
					<th class="pb-1 text-right font-semibold">{{ __("Used") }}</th>
					<th class="pb-1 text-right font-semibold">{{ __("Limit") }}</th>
					<th class="pb-1 text-right font-semibold">{{ __("Remaining") }}</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, index) in tableRows" :key="index">
					<td class="py-1 text-gray-800">{{ row.label }}</td>
					<td class="py-1 text-right text-gray-800">{{ row.used }}</td>
					<td class="py-1 text-right text-gray-800">{{ row.max }}</td>
					<td class="py-1 text-right font-semibold" :class="row.colorClass">
						{{ row.remaining }}
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { computed, inject, watch } from "vue"
import { createResource } from "frappe-ui"

const __ = inject("$translate")

const props = defineProps({
	employee: {
		type: String,
		required: false,
	},
	reason: {
		type: String,
		required: false,
	},
	fromDate: {
		type: String,
		required: false,
	},
})

// Same endpoint desk's Attendance Request form uses for the "Limit Balance"
// panel shown under the Reason field (sj_hr's client script, trigger
// refresh_limit_balance) - limits are configured per Attendance Request Type
// (day-count and/or hour-count caps per period), not tied to Leave Type.
const balance = createResource({
	url: "sj_hr.overrides.attendance_request.get_attendance_request_balance",
	auto: false,
})

const tableRows = computed(() => {
	const rows = []
	for (const row of balance.data || []) {
		if (row.max_count !== undefined) {
			rows.push({
				label: `${__(row.period_type)} (${__("days")})`,
				used: row.used_count,
				max: row.max_count,
				remaining: row.remaining_count,
				colorClass: colorClass(row.used_count, row.max_count),
			})
		}
		if (row.max_hours !== undefined) {
			rows.push({
				label: `${__(row.period_type)} (${__("hrs")})`,
				used: row.used_hours,
				max: row.max_hours,
				remaining: row.remaining_hours,
				colorClass: colorClass(row.used_hours, row.max_hours),
			})
		}
	}
	return rows
})

function colorClass(used, max) {
	const pct = max ? used / max : 0
	if (pct >= 1) return "text-red-600"
	if (pct >= 0.75) return "text-orange-600"
	return "text-green-700"
}

function refresh() {
	if (!props.employee || !props.reason || !props.fromDate) {
		balance.data = null
		return
	}
	balance.fetch({
		employee: props.employee,
		reason: props.reason,
		from_date: props.fromDate,
	})
}

watch(() => [props.employee, props.reason, props.fromDate], refresh, {
	immediate: true,
})
</script>
