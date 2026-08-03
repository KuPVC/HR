<template>
	<ListItem>
		<template #left>
			<div class="flex items-center justify-center h-8 w-8 rounded-lg bg-purple-50 shrink-0">
				<MaterialRequestIcon class="h-4 w-4 text-purple-600" />
			</div>
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ __(props.doc.material_request_type, null, "Material Request Type") }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ dayjs(props.doc.transaction_date).format("D MMM, YYYY") }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge variant="outline" :theme="colorMap[props.doc.status] || 'gray'" :label="__(props.doc.status)" size="md" />
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { inject } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import MaterialRequestIcon from "@/components/icons/MaterialRequestIcon.vue"

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
})

const colorMap = {
	Draft: "gray",
	Cancelled: "red",
	Stopped: "red",
	Completed: "green",
	Received: "green",
	Transferred: "green",
	Issued: "green",
	Ordered: "orange",
	"Partially Ordered": "orange",
	"Partially Received": "orange",
	Pending: "blue",
}
</script>
