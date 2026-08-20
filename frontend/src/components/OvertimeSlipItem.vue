<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<div
				class="flex items-center justify-center h-8 w-8 rounded-lg bg-orange-50 shrink-0"
			>
				<FeatherIcon name="clock" class="h-4 w-4 text-orange-600" />
			</div>
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ __("Overtime Slip") }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ dates }}</span>
					<span v-if="props.doc.total_overtime_duration">
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">
							{{ __("{0}h", [props.doc.total_overtime_duration]) }}
						</span>
					</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="colorMap[status]"
				:label="__(status)"
				size="md"
			/>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const props = defineProps({
	doc: {
		type: Object,
	},
	workflowStateField: {
		type: String,
		required: false,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	},
})

const dates = computed(() => {
	const start = dayjs(props.doc.start_date).format("D MMM")
	const end = props.doc.end_date
		? dayjs(props.doc.end_date).format("D MMM, YYYY")
		: ""
	return end && end !== start ? `${start} - ${end}` : start
})

const status = computed(() => {
	if (props.doc.docstatus === 2) return "Cancelled"
	return props.doc.docstatus ? "Submitted" : "Draft"
})

const colorMap = {
	Draft: "gray",
	Submitted: "blue",
	Cancelled: "red",
}
</script>
