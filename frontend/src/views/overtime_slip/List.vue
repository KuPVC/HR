<template>
	<AppShell :pageTitle="__('Overtime Slips')">
		<template #body>
			<div class="flex flex-col w-full max-w-[1600px] mx-auto gap-4">
				<div
					v-if="documents.data?.length"
					class="flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm overflow-auto w-full"
				>
					<a
						v-for="doc in documents.data"
						:key="doc.name"
						:href="`/app/overtime-slip/${doc.name}`"
						target="_blank"
						rel="noopener"
						class="flex flex-row items-center justify-between p-3.5 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
					>
						<div class="flex flex-col gap-0.5">
							<span class="text-sm font-medium text-gray-900">{{
								doc.employee_name
							}}</span>
							<span class="text-xs text-gray-500">
								{{ formatDate(doc.start_date) }} -
								{{ formatDate(doc.end_date) }}
								<span v-if="doc.total_overtime_duration">
									&middot; {{ __("{0}h", [doc.total_overtime_duration]) }}
								</span>
							</span>
						</div>
						<span
							class="text-xs font-medium px-2 py-1 rounded-full"
							:class="statusClasses(doc.docstatus)"
						>
							{{ statusLabel(doc.docstatus) }}
						</span>
					</a>
				</div>
				<EmptyState
					:message="
						canApproveTeamRequests.data === false
							? __('You do not have access to this page')
							: __('No overtime slips found')
					"
					v-else
				/>
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { inject } from "vue"
import { createResource } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import EmptyState from "@/components/EmptyState.vue"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const canApproveTeamRequests = createResource({
	url: "craft_hr.api.can_approve_team_requests",
	cache: "craft_hr:can_approve_team_requests",
	auto: true,
})

const documents = createResource({
	url: "craft_hr.api.get_team_overtime_slips",
	cache: "craft_hr:team_overtime_slips_list",
	auto: true,
})

function formatDate(date) {
	return date ? dayjs(date).format("D MMM YYYY") : ""
}

function statusLabel(docstatus) {
	if (docstatus === 2) return __("Cancelled")
	return docstatus ? __("Submitted") : __("Draft")
}

function statusClasses(docstatus) {
	if (docstatus === 2) return "bg-red-100 text-red-700"
	if (docstatus === 1) return "bg-green-100 text-green-700"
	return "bg-gray-100 text-gray-700"
}
</script>
