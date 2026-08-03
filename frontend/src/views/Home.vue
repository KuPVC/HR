<template>
	<AppShell>
		<template #body>
			<div class="flex flex-col gap-6 w-full max-w-[1600px] mx-auto">
				<div class="flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm w-full py-6 px-6">
					<h2 class="text-lg font-semibold text-gray-900">
						{{ greeting }}
					</h2>
					<div class="font-medium text-sm text-gray-500 mt-1.5">
						{{ dayjs().format("ddd, D MMMM, YYYY") }}
					</div>
				</div>

				<QuickLinks :items="quickLinks" />

				<div
					class="grid grid-cols-1 sm:grid-cols-2 gap-4"
					v-if="todaysCheckins.data?.length || estimatedCheckout.data || nextHolidays.data?.length"
				>
					<div
						v-if="todaysCheckins.data?.length || estimatedCheckout.data"
						class="flex flex-col gap-4 rounded-xl border border-blue-200 bg-blue-100 shadow-sm p-5"
					>
						<div v-if="todaysCheckins.data?.length" class="flex flex-col gap-3">
							<div class="flex items-center gap-2">
								<div class="flex items-center justify-center h-8 w-8 rounded-full bg-blue-200">
									<FeatherIcon name="clock" class="h-4 w-4 text-blue-800" />
								</div>
								<div class="text-sm font-semibold text-blue-900">{{ __("Today's Check-in") }}</div>
							</div>
							<div class="flex flex-wrap gap-2">
								<Badge
									v-for="log in todaysCheckins.data"
									:key="log.name"
									:theme="log.log_type == 'IN' ? 'green' : 'orange'"
									variant="subtle"
									size="md"
									:label="`${log.log_type} · ${dayjs(log.time).format('h:mm A')}`"
								/>
							</div>
						</div>

						<hr v-if="todaysCheckins.data?.length && estimatedCheckout.data" class="border-blue-200" />

						<div v-if="estimatedCheckout.data" class="flex flex-col gap-2">
							<div class="flex items-center gap-2">
								<div class="flex items-center justify-center h-8 w-8 rounded-full bg-purple-200">
									<FeatherIcon name="log-out" class="h-4 w-4 text-purple-800" />
								</div>
								<div class="text-sm font-semibold text-purple-900">{{ __("Estimated Check-out") }}</div>
							</div>
							<div class="text-base font-medium text-purple-900">
								{{ dayjs(estimatedCheckout.data.estimated_checkout).format("h:mm A") }}
							</div>
							<div class="text-xs text-purple-800">
								{{ __("Based on {0} required hours", [estimatedCheckout.data.required_hours]) }}
							</div>
						</div>
					</div>

					<div
						v-if="nextHolidays.data?.length"
						class="flex flex-col gap-3 rounded-xl border border-orange-200 bg-orange-100 shadow-sm p-5"
					>
						<div class="flex items-center gap-2">
							<div class="flex items-center justify-center h-8 w-8 rounded-full bg-orange-200">
								<FeatherIcon name="sun" class="h-4 w-4 text-orange-800" />
							</div>
							<div class="text-sm font-semibold text-orange-900">{{ __("Upcoming Holidays") }}</div>
						</div>
						<div
							v-for="holiday in nextHolidays.data"
							:key="holiday.holiday_date"
							class="flex flex-row items-baseline gap-2"
						>
							<span class="text-sm font-medium text-orange-900">
								{{ dayjs(holiday.holiday_date).format("ddd, D MMM YYYY") }}
							</span>
							<span class="text-xs text-orange-800" v-if="holiday.description">
								{{ holiday.description }}
							</span>
						</div>
					</div>
				</div>

				<RequestPanel />
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { inject, computed } from "vue"
import { Badge, FeatherIcon, createResource } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import QuickLinks from "@/components/QuickLinks.vue"
import RequestPanel from "@/components/RequestPanel.vue"

import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import MaterialRequestIcon from "@/components/icons/MaterialRequestIcon.vue"

const __ = inject("$translate")
const dayjs = inject("$dayjs")
const employee = inject("$employee")

const todaysCheckins = createResource({
	url: "craft_hr.api.get_todays_checkins",
	cache: "craft_hr:todays_checkins",
	auto: true,
})

const nextHolidays = createResource({
	url: "craft_hr.api.get_next_holidays",
	cache: "craft_hr:next_holidays",
	auto: true,
})

const estimatedCheckout = createResource({
	url: "craft_hr.api.get_todays_estimated_checkout",
	cache: "craft_hr:estimated_checkout",
	auto: true,
})

const greeting = computed(() => {
	const hour = dayjs().hour()
	const name = employee?.data?.first_name
	if (hour < 12) return __("Good morning, {0}", [name])
	if (hour < 17) return __("Good afternoon, {0}", [name])
	return __("Good evening, {0}", [name])
})

const quickLinks = [
	{
		title: __("Attendance Request"),
		icon: AttendanceIcon,
		route: "AttendanceRequestFormView",
	},
	{
		title: __("Leave Application"),
		icon: LeaveIcon,
		route: "LeaveApplicationFormView",
	},
	{
		title: __("Salary Slips"),
		icon: SalaryIcon,
		route: "SalarySlipsDashboard",
	},
	{
		title: __("Create Material Request"),
		icon: MaterialRequestIcon,
		href: "/app/material-request/new",
	},
]
</script>
