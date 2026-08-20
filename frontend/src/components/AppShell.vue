<template>
	<div class="min-h-screen w-full bg-gray-50 flex flex-col">
		<!-- Top nav -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-40">
			<div
				class="w-full px-4 md:px-8 flex flex-row items-center justify-between h-16"
			>
				<div class="flex flex-row items-center gap-3">
					<span
						v-if="employee?.data?.company"
						class="text-lg font-semibold text-gray-900"
					>
						{{ employee.data.company }}
					</span>
					<span v-else class="h-5 w-40 rounded bg-gray-100 animate-pulse" />
				</div>

				<div class="flex flex-row items-center gap-4">
					<router-link :to="{ name: 'Notifications' }" class="relative">
						<FeatherIcon name="bell" class="h-5 w-5 text-gray-600" />
						<span
							v-if="unreadNotificationsCount.data"
							class="absolute -top-0.5 -right-0.5 inline-block w-2 h-2 bg-red-600 rounded-full border border-white"
						/>
					</router-link>
					<router-link
						:to="{ name: 'Profile' }"
						class="flex flex-row items-center gap-2"
					>
						<Avatar
							:image="user.data?.user_image"
							:label="user.data?.first_name"
							size="lg"
						/>
						<span class="hidden sm:inline text-sm font-medium text-gray-800">
							{{ user.data?.first_name }}
						</span>
					</router-link>
				</div>
			</div>
		</header>

		<div class="flex flex-1 w-full max-w-[1600px] mx-auto">
			<!-- Sidebar (desktop/tablet) -->
			<aside
				class="hidden md:flex md:flex-col w-56 shrink-0 border-r border-gray-200 bg-white px-3 py-6 gap-1"
			>
				<router-link
					v-for="link in navLinks"
					:key="link.name"
					:to="{ name: link.name }"
					class="flex flex-row items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
					:class="
						isActive(link)
							? 'bg-gray-900 text-white'
							: 'text-gray-700 hover:bg-gray-100'
					"
				>
					<component :is="link.icon" class="h-4 w-4" />
					{{ link.label }}
				</router-link>
			</aside>

			<!-- Main content -->
			<main class="flex-1 min-w-0 px-6 py-6 md:px-10 pb-20 md:pb-6">
				<h1 v-if="pageTitle" class="text-2xl font-semibold text-gray-900 mb-6">
					{{ pageTitle }}
				</h1>
				<slot name="body" />
			</main>
		</div>

		<!-- Bottom tab bar (mobile) -->
		<nav
			class="md:hidden fixed bottom-0 inset-x-0 z-40 flex flex-row border-t border-gray-200 bg-white"
		>
			<router-link
				v-for="link in navLinks"
				:key="link.name"
				:to="{ name: link.name }"
				class="flex-1 flex flex-col items-center justify-center gap-1 py-2 px-1 text-xs font-medium"
				:class="isActive(link) ? 'text-gray-900' : 'text-gray-500'"
			>
				<component :is="link.icon" class="h-5 w-5 shrink-0" />
				<span class="w-full text-center leading-tight">{{ link.label }}</span>
			</router-link>
		</nav>
	</div>
</template>

<script setup>
import { inject, computed } from "vue"
import { useRoute } from "vue-router"
import { Avatar, FeatherIcon, createResource } from "frappe-ui"

import { unreadNotificationsCount } from "@/data/notifications"

import HomeIcon from "@/components/icons/HomeIcon.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import MaterialRequestIcon from "@/components/icons/MaterialRequestIcon.vue"
import OvertimeSlipIcon from "@/components/icons/OvertimeSlipIcon.vue"

const __ = inject("$translate")
const user = inject("$user")
const employee = inject("$employee")
const route = useRoute()

defineProps({
	pageTitle: {
		type: String,
		required: false,
		default: "",
	},
})

// Same manager-only gate as the Team Requests tab on Home - Overtime Slip
// is only relevant to people with reports, so it's hidden from the nav
// entirely rather than shown as an empty page for everyone.
const canApproveTeamRequests = createResource({
	url: "craft_hr.api.can_approve_team_requests",
	cache: "craft_hr:can_approve_team_requests",
	auto: true,
})

const navLinks = computed(() => {
	const links = [
		{ name: "Home", label: __("Home"), icon: HomeIcon },
		{
			name: "AttendanceDashboard",
			label: __("Attendance"),
			icon: AttendanceIcon,
		},
		{ name: "LeavesDashboard", label: __("Leaves"), icon: LeaveIcon },
		{
			name: "SalarySlipsDashboard",
			label: __("Salary Slips"),
			icon: SalaryIcon,
		},
		{
			name: "MaterialRequestListView",
			label: __("Material Request"),
			icon: MaterialRequestIcon,
		},
	]
	if (canApproveTeamRequests.data) {
		links.push({
			name: "OvertimeSlipListView",
			label: __("Overtime Slip"),
			icon: OvertimeSlipIcon,
		})
	}
	return links
})

function isActive(link) {
	return route.name === link.name
}
</script>
