<template>
	<AppShell :pageTitle="__('Attendance')">
		<template #body>
			<div class="flex flex-col gap-7 w-full max-w-[1600px] mx-auto">
				<TabButtons
					v-if="canApproveTeamRequests.data"
					:buttons="['My Attendance', 'Team Calendar']"
					v-model="activeTab"
				/>

				<template v-if="activeTab == 'My Attendance'">
					<AttendanceCalendar />
					<div class="w-full max-w-xs">
						<router-link
							:to="{ name: 'AttendanceRequestFormView' }"
							v-slot="{ navigate }"
						>
							<Button
								@click="navigate"
								variant="solid"
								class="w-full py-5 text-base"
							>
								{{ __("Request Attendance") }}
							</Button>
						</router-link>
					</div>
					<div>
						<div class="text-lg text-gray-900 font-semibold">
							{{ __("Recent Attendance Requests") }}
						</div>
						<RequestList
							:component="markRaw(AttendanceRequestItem)"
							:items="myAttendanceRequests?.data?.slice(0, 5)"
							:addListButton="true"
							:listButtonRoute="__('AttendanceRequestListView')"
						/>
					</div>
					<div>
						<div class="text-lg text-gray-900 font-semibold">
							{{ __("Upcoming Shifts") }}
						</div>
						<RequestList
							:component="markRaw(ShiftAssignmentItem)"
							:items="upcomingShifts"
							:emptyStateMessage="__('You have no upcoming shifts')"
						/>
					</div>
				</template>

				<TeamAttendanceCalendar v-else-if="activeTab == 'Team Calendar'" />
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { computed, inject, markRaw, onMounted, ref } from "vue"
import { createResource } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ShiftAssignmentItem from "@/components/ShiftAssignmentItem.vue"
import RequestList from "@/components/RequestList.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
import TeamAttendanceCalendar from "@/components/TeamAttendanceCalendar.vue"
import TabButtons from "@/components/TabButtons.vue"

import {
	getShiftDates,
	getTotalShiftDays,
	getShiftTiming,
	myAttendanceRequests,
} from "@/data/attendance"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const activeTab = ref("My Attendance")

// Same manager-only gate as Team Requests / Overtime Slip.
const canApproveTeamRequests = createResource({
	url: "craft_hr.api.can_approve_team_requests",
	cache: "craft_hr:can_approve_team_requests",
	auto: true,
})

const shifts = createResource({
	url: "hrms.api.get_shifts",
	auto: true,
	cache: "craft_hr:shifts",
	transform: (data) => {
		return data.map((assignment) => {
			assignment.doctype = "Shift Assignment"
			assignment.is_upcoming =
				!assignment.end_date || dayjs(assignment.end_date).isAfter(dayjs())
			assignment.shift_dates = getShiftDates(assignment)
			assignment.total_shift_days = getTotalShiftDays(assignment)
			assignment.shift_timing = getShiftTiming(assignment)
			return assignment
		})
	},
})

const upcomingShifts = computed(() => {
	const filteredShifts = shifts.data?.filter((shift) => shift.is_upcoming)

	// show only 5 upcoming shifts
	return filteredShifts?.slice(0, 5)
})

// myAttendanceRequests is a shared module-level resource (cached by
// `cache:` key) - importing it here doesn't refetch it, so reload
// explicitly on every visit to this page.
onMounted(() => {
	myAttendanceRequests.reload()
})
</script>
