<template>
	<AppShell :pageTitle="__('Material Requests')">
		<template #body>
			<div class="flex flex-col w-full max-w-[1600px] mx-auto gap-4">
				<div class="flex flex-row items-center justify-end">
					<a href="/app/material-request/new">
						<Button variant="solid">
							<template #prefix>
								<FeatherIcon name="plus" class="h-4 w-4" />
							</template>
							{{ __("New Material Request") }}
						</Button>
					</a>
				</div>

				<div
					v-if="documents.data?.length"
					class="flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm overflow-auto w-full"
				>
					<a
						v-for="doc in documents.data"
						:key="doc.name"
						:href="`/app/material-request/${doc.name}`"
						target="_blank"
						rel="noopener"
						class="flex flex-row items-center justify-between p-3.5 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
					>
						<div class="flex flex-col gap-0.5">
							<span class="text-sm font-medium text-gray-900">{{ doc.name }}</span>
							<span class="text-xs text-gray-500">
								{{ doc.material_request_type }} · {{ formatDate(doc.transaction_date) }}
							</span>
						</div>
						<span
							class="text-xs font-medium px-2 py-1 rounded-full"
							:class="statusClasses(doc.status)"
						>
							{{ doc.status }}
						</span>
					</a>
				</div>
				<EmptyState :message="__('No material requests found')" v-else />
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { inject } from "vue"
import { Button, FeatherIcon, createListResource } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import EmptyState from "@/components/EmptyState.vue"

const __ = inject("$translate")
const dayjs = inject("$dayjs")
const user = inject("$user")

const documents = createListResource({
	doctype: "Material Request",
	fields: ["name", "transaction_date", "material_request_type", "status"],
	filters: {
		owner: user.data?.name,
	},
	orderBy: "creation desc",
	pageLength: 50,
	auto: true,
})

function formatDate(date) {
	return date ? dayjs(date).format("D MMM YYYY") : ""
}

function statusClasses(status) {
	if (["Completed", "Received", "Transferred", "Issued"].includes(status)) {
		return "bg-green-100 text-green-700"
	}
	if (status === "Cancelled") {
		return "bg-red-100 text-red-700"
	}
	if (status === "Partially Ordered" || status === "Partially Received") {
		return "bg-amber-100 text-amber-700"
	}
	return "bg-gray-100 text-gray-700"
}
</script>
