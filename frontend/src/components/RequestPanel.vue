<template>
	<div class="w-full">
		<TabButtons
			:buttons="TAB_BUTTONS"
			v-model="activeTab"
		/>
		<RequestList v-if="activeTab == 'My Requests'" :items="myRequests" />
		<RequestList
			v-else-if="activeTab == 'Team Requests'"
			:items="teamRequests"
			:teamRequests="true"
		/>
	</div>
</template>

<script setup>
import { ref, inject, onMounted, computed, markRaw } from "vue"
import { createResource } from "frappe-ui"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myAttendanceRequests, myShiftRequests, teamShiftRequests, teamAttendanceRequests } from "@/data/attendance"
import { myLeaves, teamLeaves } from "@/data/leaves"
import { myMaterialRequests } from "@/data/material_requests"

import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import MaterialRequestItem from "@/components/MaterialRequestItem.vue"

import { useListUpdate } from "@/composables/realtime"

const activeTab = ref("My Requests")
const socket = inject("$socket")

const canApproveTeamRequests = createResource({
	url: "craft_hr.api.can_approve_team_requests",
	cache: "craft_hr:can_approve_team_requests",
	auto: true,
})

const TAB_BUTTONS = computed(() =>
	canApproveTeamRequests.data ? ["My Requests", "Team Requests"] : ["My Requests"]
) // __("My Requests"), __("Team Requests")

const myRequests = computed(() =>
	updateRequestDetails(
		[myLeaves, myShiftRequests, myAttendanceRequests, myMaterialRequests],
		{
			"Leave Application": LeaveRequestItem,
			"Shift Request": ShiftRequestItem,
			"Attendance Request": AttendanceRequestItem,
			"Material Request": MaterialRequestItem,
		}
	)
)

const teamRequests = computed(() =>
	updateRequestDetails(
		[teamLeaves, teamShiftRequests, teamAttendanceRequests],
		{
			"Leave Application": LeaveRequestItem,
			"Shift Request": ShiftRequestItem,
			"Attendance Request": AttendanceRequestItem,
		}
	)
)

function updateRequestDetails(resources, componentMap) {
	const requests = resources.reduce(
		(acc, resource) => acc.concat(resource?.data || []),
		[]
	)

	requests.forEach((request) => {
		request.component = markRaw(componentMap[request.doctype])
	})

	return getSortedRequests(requests)
}

function getSortedRequests(list) {
	// return top 10 requests sorted by posting date
	return list
		.sort((a, b) => {
			return new Date(b.creation) - new Date(a.creation)
		})
		.splice(0, 10)
}

onMounted(() => {
	useListUpdate(socket, "Leave Application", () => teamLeaves.reload())
	useListUpdate(socket, "Shift Request", () => teamShiftRequests.reload())
	useListUpdate(socket, "Attendance Request", () => teamAttendanceRequests.reload())
})
</script>
