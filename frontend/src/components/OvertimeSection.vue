<template>
	<div class="flex flex-col w-full gap-4">
		<!-- Title + create button -->
		<div class="flex flex-row items-center justify-between gap-3">
			<div class="text-lg text-gray-800 font-bold">
				{{ __("Overtime") }}
			</div>
			<Button variant="solid" @click="createSlip">
				{{ __("Create Overtime Slip") }}
			</Button>
		</div>

		<div class="flex flex-col gap-4 bg-white py-4 px-3.5 rounded-lg">
			<!-- Salary period switcher -->
			<div class="flex flex-row justify-between items-center px-2">
				<Button icon="chevron-left" variant="ghost" @click="offset -= 1" />
				<div class="flex flex-col items-center">
					<span class="text-base text-gray-800 font-bold text-center">
						{{ periodLabel }}
					</span>
					<span class="text-xs text-gray-500">
						{{ offset === 0 ? __("Current salary period") : __("Salary period") }}
					</span>
				</div>
				<Button icon="chevron-right" variant="ghost" @click="offset += 1" />
			</div>

			<!-- Who / what tabs -->
			<div v-if="overview.data?.has_team" class="flex p-0.5 bg-gray-200 rounded">
				<button
					v-for="tab in tabs"
					:key="tab.key"
					type="button"
					class="px-3 py-1.5 transition-all rounded-md flex-auto text-sm font-medium"
					:class="
						activeTab === tab.key
							? 'bg-white drop-shadow text-gray-900'
							: 'text-gray-600'
					"
					@click="selectTab(tab.key)"
				>
					{{ tab.label }}
				</button>
			</div>

			<div v-if="overview.loading && !overview.data" class="text-sm text-gray-500 p-4">
				{{ __("Loading...") }}
			</div>

			<template v-else-if="overview.data">
				<!-- Per-day overview -->
				<div class="flex flex-col gap-2">
					<div class="flex flex-row items-baseline justify-between">
						<span class="text-sm font-semibold text-gray-700">
							{{ __("Overtime by day") }}
						</span>
						<span class="text-xs text-gray-500">
							{{ summaryText }}
						</span>
					</div>
					<div class="flex flex-row flex-wrap gap-1">
						<button
							v-for="day in periodDays"
							:key="day.key"
							type="button"
							class="flex flex-col items-center justify-center w-11 h-12 rounded border text-xs leading-tight"
							:class="dayCellClass(day)"
							:disabled="!day.entries.length"
							:title="dayTitle(day)"
							@click="selectedDay = selectedDay === day.key ? null : day.key"
						>
							<span class="text-[10px] uppercase">{{ day.weekday }}</span>
							<span class="font-semibold">{{ day.dayOfMonth }}</span>
							<span v-if="day.entries.length" class="font-bold">
								{{ activeTab === "team" ? day.entries.length : formatHours(day.hours) }}
							</span>
						</button>
					</div>
					<div class="text-[11px] text-gray-500">
						{{
							activeTab === "team"
								? __("Number shown = people with overtime that day. Click a day for names.")
								: __("Number shown = overtime hours that day.")
						}}
					</div>

					<div
						v-if="selectedDay && selectedDayEntries.length"
						class="rounded-lg border border-gray-200 p-2.5 flex flex-col gap-1"
					>
						<div class="text-xs font-semibold text-gray-700">
							{{ dayjs(selectedDay).format("dddd, D MMM YYYY") }} &middot;
							{{ __("{0} with overtime", [selectedDayEntries.length]) }}
						</div>
						<div
							v-for="entry in selectedDayEntries"
							:key="entry.employee"
							class="flex flex-row justify-between text-sm text-gray-800"
						>
							<span class="truncate">{{ entry.employee_name }}</span>
							<span class="shrink-0 font-medium">{{ formatHours(entry.hours) }}</span>
						</div>
					</div>
				</div>

				<!-- My overtime: slips -->
				<div v-if="activeTab === 'self'" class="flex flex-col gap-2">
					<div class="text-sm font-semibold text-gray-700">
						{{ __("Overtime Slips") }}
					</div>
					<template v-if="overview.data.self.slips.length">
						<SlipRow
							v-for="slip in overview.data.self.slips"
							:key="slip.name"
							:slip="slip"
							:showName="false"
						/>
					</template>
					<EmptyState v-else :message="__('No overtime slips in this salary period')" />
				</div>

				<!-- Team overtime: grouped by employee -->
				<div v-else class="flex flex-col gap-3">
					<div class="text-sm font-semibold text-gray-700">
						{{ __("Overtime Slips by employee") }}
					</div>
					<template v-if="overview.data.team.employees.length">
						<div
							v-for="group in overview.data.team.employees"
							:key="group.employee"
							class="flex flex-col gap-1"
						>
							<div
								class="flex flex-row items-center justify-between gap-2 border-b border-gray-200 pb-1"
							>
								<div class="flex flex-row items-center gap-2 min-w-0">
									<Avatar :label="group.employee_name" size="xs" />
									<span class="truncate text-sm font-semibold text-gray-800">
										{{ group.employee_name }}
									</span>
								</div>
								<span class="shrink-0 text-xs text-gray-600">
									{{ __("{0} slip(s)", [group.slips.length]) }} &middot;
									<b>{{ formatHours(group.total_hours) }}</b>
								</span>
							</div>
							<SlipRow
								v-for="slip in group.slips"
								:key="slip.name"
								:slip="slip"
								:showName="false"
							/>
						</div>
					</template>
					<EmptyState v-else :message="__('No overtime slips for your team in this salary period')" />
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, h, inject, ref, watch } from "vue"
import { Avatar, Button, createResource } from "frappe-ui"

import EmptyState from "@/components/EmptyState.vue"
import { stateClasses, stateLabel } from "@/utils/workflow"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const offset = ref(0)
const activeTab = ref("self")
const selectedDay = ref(null)

const overview = createResource({
	url: "craft_hr.api.get_overtime_overview",
	makeParams() {
		return { offset: offset.value }
	},
	auto: true,
})

watch(offset, () => {
	selectedDay.value = null
	overview.fetch()
})

const tabs = computed(() => [
	{ key: "self", label: __("My Overtime") },
	{ key: "team", label: __("Team Overtime") },
])

function selectTab(key) {
	activeTab.value = key
	selectedDay.value = null
}

const periodLabel = computed(() => {
	const data = overview.data
	if (!data) return ""
	return `${dayjs(data.period_start).format("D MMM YYYY")} - ${dayjs(data.period_end).format("D MMM YYYY")}`
})

const activeBucket = computed(() =>
	overview.data ? overview.data[activeTab.value === "team" ? "team" : "self"] : null
)

// every date of the salary period, with that day's overtime entries (if any)
const periodDays = computed(() => {
	const data = overview.data
	if (!data) return []
	const daily = activeBucket.value?.daily || {}
	const start = dayjs(data.period_start)
	const total = dayjs(data.period_end).diff(start, "day") + 1
	const days = []
	for (let i = 0; i < total; i++) {
		const date = start.add(i, "day")
		const key = date.format("YYYY-MM-DD")
		const entries = daily[key] || []
		days.push({
			key,
			weekday: date.format("dd"),
			dayOfMonth: date.format("D"),
			entries,
			hours: entries.reduce((sum, e) => sum + e.hours, 0),
		})
	}
	return days
})

const selectedDayEntries = computed(
	() => periodDays.value.find((d) => d.key === selectedDay.value)?.entries || []
)

const summaryText = computed(() => {
	const bucket = activeBucket.value
	if (!bucket) return ""
	const daysWithOvertime = periodDays.value.filter((d) => d.entries.length).length
	return `${__("{0} day(s)", [daysWithOvertime])} · ${formatHours(bucket.total_hours)}`
})

function dayCellClass(day) {
	if (!day.entries.length) return "border-gray-100 text-gray-400 cursor-default"
	const intensity = activeTab.value === "team" ? day.entries.length : day.hours
	const level = intensity >= 6 ? "bg-purple-300" : intensity >= 3 ? "bg-purple-200" : "bg-purple-100"
	const ring = selectedDay.value === day.key ? "border-purple-600" : "border-purple-200"
	return `${level} ${ring} text-gray-900 cursor-pointer`
}

function dayTitle(day) {
	if (!day.entries.length) return ""
	return day.entries.map((e) => `${e.employee_name}: ${formatHours(e.hours)}`).join("\n")
}

function formatHours(hours) {
	return `${Number(hours || 0).toFixed(2).replace(/\.?0+$/, "")}h`
}

// Overtime Slip form on the desk: for yourself the employee is pre-filled,
// for the team you pick the employee there.
function createSlip() {
	let url = "/app/overtime-slip/new"
	if (activeTab.value === "self" && overview.data?.employee) {
		url += `?employee=${encodeURIComponent(overview.data.employee)}`
	}
	window.open(url, "_blank")
}

// one slip row (opens the slip on the desk) with its in-period overtime days
const SlipRow = {
	props: {
		slip: { type: Object, required: true },
		showName: { type: Boolean, default: true },
	},
	setup(props) {
		return () => {
			const slip = props.slip
			return h(
				"a",
				{
					href: `/app/overtime-slip/${encodeURIComponent(slip.name)}`,
					target: "_blank",
					rel: "noopener",
					class:
						"flex flex-col gap-1 rounded-md border border-gray-100 px-2.5 py-1.5 hover:bg-gray-50",
				},
				[
					h("div", { class: "flex flex-row items-center justify-between gap-2" }, [
						h("div", { class: "flex flex-col min-w-0" }, [
							h("span", { class: "text-sm font-medium text-gray-900 truncate" }, slip.name),
							h(
								"span",
								{ class: "text-xs text-gray-500" },
								`${dayjs(slip.start_date).format("D MMM")} - ${dayjs(slip.end_date).format("D MMM YYYY")}`
							),
						]),
						h("div", { class: "flex flex-row items-center gap-2 shrink-0" }, [
							h(
								"span",
								{ class: "text-sm font-semibold text-gray-800" },
								formatHours(slip.period_hours)
							),
							h(
								"span",
								{ class: `text-xs font-medium px-2 py-0.5 rounded-full ${stateClasses(slip)}` },
								stateLabel(slip, __)
							),
						]),
					]),
					slip.details.length
						? h(
								"div",
								{ class: "flex flex-row flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-gray-600" },
								slip.details.map((d) =>
									h("span", { key: d.date + d.overtime_type }, [
										h("span", { class: "font-medium" }, dayjs(d.date).format("D MMM")),
										` ${formatHours(d.hours)}`,
										d.overtime_type ? ` (${d.overtime_type})` : "",
									])
								)
							)
						: null,
				]
			)
		}
	},
}
</script>
