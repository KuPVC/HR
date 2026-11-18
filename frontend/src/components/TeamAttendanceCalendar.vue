<template>
	<div class="flex flex-col w-full gap-5" v-if="teamCalendar.data">
		<div class="text-lg text-gray-800 font-bold">
			{{ __("Team Attendance Calendar") }}
		</div>

		<div
			class="flex flex-col gap-6 bg-white py-6 px-3.5 rounded-lg border-none"
		>
			<!-- Period Change -->
			<div class="flex flex-row justify-between items-center px-4">
				<Button
					icon="chevron-left"
					variant="ghost"
					@click="cursorMonth = cursorMonth.subtract(1, 'M')"
				/>
				<span class="text-lg text-gray-800 font-bold text-center">
					{{ cursorMonth.format("MMMM YYYY") }}
				</span>
				<Button
					icon="chevron-right"
					variant="ghost"
					@click="cursorMonth = cursorMonth.add(1, 'M')"
				/>
			</div>

			<!-- Calendar -->
			<div class="grid grid-cols-7 gap-y-3">
				<div
					v-for="day in DAYS"
					:key="day"
					class="flex justify-center text-gray-600 text-sm font-medium leading-6"
				>
					{{ day }}
				</div>
				<div v-for="n in leadingOffset" :key="`blank-${n}`" />
				<div
					v-for="cellDate in periodDates"
					:key="cellDate.format('YYYY-MM-DD')"
				>
					<button
						type="button"
						class="relative h-9 w-9 mx-auto block cursor-pointer"
						@click="handleDateClick(cellDate)"
					>
						<div
							class="h-8 w-8 flex rounded-full mx-auto"
							:class="isCarryOver(cellDate) ? 'opacity-40' : ''"
							:style="cellStyle(cellDate)"
						>
							<span
								class="text-gray-800 text-sm font-medium m-auto"
								:class="
									isToday(cellDate)
										? 'underline decoration-2 underline-offset-2'
										: ''
								"
							>
								{{ cellDate.format("D") }}
							</span>
						</div>
						<span
							v-if="isChecked(cellDate)"
							class="absolute -top-0.5 right-0 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-green-600 text-white ring-2 ring-white"
							:title="__('Checked')"
						>
							<FeatherIcon name="check" class="h-2.5 w-2.5" />
						</span>
					</button>
				</div>
			</div>
		</div>

		<div class="flex flex-row items-center gap-1.5 px-1 text-xs text-gray-500">
			<FeatherIcon name="info" class="h-3.5 w-3.5 shrink-0" />
			<span>{{
				__("Tip: click on any date to see who needs attention and who has no issues. Tick \"Checked\" once you have gone through a date - it shows a green tick on the calendar.")
			}}</span>
		</div>

		<Dialog
			v-model="showDayDialog"
			:options="{ title: selectedDateLabel, size: 'lg' }"
		>
			<template #body-content>
				<!-- Personal "I have gone through this date" marker -->
				<label
					class="flex items-center gap-2 mb-3 text-sm text-gray-800 cursor-pointer select-none"
				>
					<input
						type="checkbox"
						class="h-4 w-4 rounded border-gray-300"
						:checked="isChecked(selectedDate)"
						@change="toggleChecked($event.target.checked)"
					/>
					<span class="font-medium">{{ __("Checked") }}</span>
					<span class="text-xs text-gray-500">
						{{ __("Tick once you have gone through this date") }}
					</span>
				</label>

				<!-- Tabs: only shown when the day has issues (otherwise there is only one list) -->
				<div v-if="hasIssues" class="flex p-0.5 mb-3 bg-gray-200 rounded">
					<button
						v-for="tab in dayTabs"
						:key="tab.key"
						type="button"
						class="px-3 py-1.5 transition-all rounded-md flex-auto text-sm font-medium"
						:class="
							activeDayTab === tab.key
								? 'bg-white drop-shadow text-gray-900'
								: 'text-gray-600'
						"
						@click="activeDayTab = tab.key"
					>
						{{ tab.label }} ({{ tab.count }})
					</button>
				</div>

				<!-- Scrollable list -->
				<div class="max-h-[55vh] overflow-y-auto pr-1">
					<div v-if="visibleCategories.length" class="flex flex-col gap-3">
						<div
							v-for="category in visibleCategories"
							:key="category.key"
							class="flex flex-col gap-1"
						>
							<div
								class="sticky top-0 z-10 bg-white py-0.5 text-xs font-semibold uppercase tracking-wide text-gray-500"
							>
								{{ category.label }} ({{ category.items.length }})
							</div>
							<div
								v-for="item in category.items"
								:key="`${category.key}-${item.employee}`"
								class="flex flex-col rounded-md border border-gray-100 px-2 py-1"
							>
								<div class="flex flex-row items-center justify-between gap-2">
									<div class="flex flex-row items-center gap-2 min-w-0">
										<Avatar :label="item.employee_name" size="xs" />
										<div class="flex flex-col min-w-0">
											<span class="truncate text-sm text-gray-800 leading-tight">
												{{ item.employee_name }}
											</span>
											<span
												v-if="rowDetail(item)"
												class="truncate text-xs text-gray-500 leading-tight"
											>
												{{ rowDetail(item) }}
											</span>
										</div>
									</div>
									<div class="flex flex-row gap-1 shrink-0">
										<Button
											size="sm"
											variant="subtle"
											:title="__('Open attendance')"
											@click="openAttendance(item)"
										>
											+
										</Button>
										<Button
											v-if="category.key !== 'no_issues'"
											size="sm"
											variant="outline"
											:title="__('Attendance Request')"
											@click="
												raiseRequest('attendance-request', item.employee, item)
											"
										>
											{{ __("AR") }}
										</Button>
										<Button
											v-if="category.key !== 'no_issues'"
											size="sm"
											variant="outline"
											:title="__('Leave Application')"
											@click="
												raiseRequest('leave-application', item.employee, item)
											"
										>
											{{ __("LA") }}
										</Button>
									</div>
								</div>
							</div>
						</div>
					</div>
					<EmptyState
						v-else
						:message="
							selectedDay
								? __('Nothing to show for this date')
								: __('No attendance records for this date')
						"
					/>
				</div>

				<!-- Abbreviations -->
				<div
					class="mt-3 border-t border-gray-100 pt-2 text-xs text-gray-500 flex flex-row flex-wrap gap-x-4 gap-y-0.5"
				>
					<span><b>+</b> = {{ __("Open the attendance") }}</span>
					<template v-if="showActionLegend">
						<span><b>AR</b> = {{ __("Attendance Request") }}</span>
						<span><b>LA</b> = {{ __("Leave Application") }}</span>
					</template>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { Avatar, Button, Dialog, FeatherIcon, createResource } from "frappe-ui"

import EmptyState from "@/components/EmptyState.vue"
import { formatHoursDuration } from "@/utils/formatters"

const dayjs = inject("$dayjs")
const __ = inject("$translate")

// Same "Monthly-25" payroll period convention as the personal
// AttendanceCalendar, for consistency across the app.
const cursorMonth = ref(dayjs().date(1).startOf("D"))
const today = dayjs().startOf("day")

const periodEnd = computed(() => cursorMonth.value.endOf("month"))
const periodStart = computed(() => cursorMonth.value.subtract(1, "M").date(25))

const periodDates = computed(() => {
	const dates = []
	const totalDays = periodEnd.value.diff(periodStart.value, "day") + 1
	for (let i = 0; i < totalDays; i++) {
		dates.push(periodStart.value.add(i, "day"))
	}
	return dates
})

const leadingOffset = computed(() => periodStart.value.day())

function isCarryOver(date) {
	return date.isBefore(cursorMonth.value, "day")
}

function isToday(date) {
	return date.isSame(today, "day")
}

function getDay(date) {
	return teamCalendar.data?.days?.[date.format("YYYY-MM-DD")]
}

// green: nobody flagged · red: at least one absence · yellow: other issues
// only (late/short hours/missed punch) with nobody absent
function dayColor(date) {
	const day = getDay(date)
	if (!day) return "green"
	if (day.absent.length) return "red"
	if (day.late.length || day.short_hours.length || day.missed_punch.length)
		return "yellow"
	return "green"
}

const COLOR_RGB = {
	green: "34, 197, 94",
	yellow: "234, 179, 8",
	red: "239, 68, 68",
}

function cellStyle(date) {
	if (date.isAfter(today, "day")) return {}

	const rgb = COLOR_RGB[dayColor(date)]

	return {
		background: `radial-gradient(circle, rgba(${rgb}, 1) 0%, rgba(${rgb}, 0.8) 65%, rgba(${rgb}, 0.35) 100%)`,
	}
}

const showDayDialog = ref(false)
const selectedDate = ref(null)

const selectedDateLabel = computed(() =>
	selectedDate.value ? selectedDate.value.format("D MMMM YYYY") : ""
)

const CATEGORY_LABELS = {
	// __("Absent"), __("Late"), __("Short Hours"), __("Missed Punch")
	absent: "Absent",
	late: "Late",
	short_hours: "Short Hours",
	missed_punch: "Missed Punch",
}

const ISSUE_KEYS = Object.keys(CATEGORY_LABELS)

const selectedDay = computed(() =>
	selectedDate.value ? getDay(selectedDate.value) : null
)

const issueCategories = computed(() => {
	const day = selectedDay.value
	if (!day) return []
	return ISSUE_KEYS.map((key) => ({
		key,
		label: __(CATEGORY_LABELS[key]),
		items: day[key] || [],
	})).filter((category) => category.items.length)
})

const noIssueItems = computed(() => selectedDay.value?.no_issues || [])
const hasIssues = computed(() => issueCategories.value.length > 0)

// "issues" = employees needing action; "clear" = attendance recorded, nothing flagged
const activeDayTab = ref("issues")

const issueCount = computed(() => selectedDay.value?.issue_count || 0)

const dayTabs = computed(() => [
	{ key: "issues", label: __("Needs Attention"), count: issueCount.value },
	{ key: "clear", label: __("No Issues"), count: noIssueItems.value.length },
])

const visibleCategories = computed(() => {
	if (activeDayTab.value === "issues" && hasIssues.value) return issueCategories.value
	return noIssueItems.value.length
		? [{ key: "no_issues", label: __("No Issues"), items: noIssueItems.value }]
		: []
})

function rowDetail(item) {
	const parts = []
	if (item.in_time || item.out_time) {
		parts.push(
			`${__("In")}: ${item.in_time ? dayjs(item.in_time).format("h:mm A") : "-"} · ${__("Out")}: ${
				item.out_time ? dayjs(item.out_time).format("h:mm A") : "-"
			}`
		)
	}
	if (item.hours_difference) {
		parts.push(__("Short by {0}", [formatHoursDuration(item.hours_difference)]))
	}
	if (!parts.length && item.status) parts.push(__(item.status))
	return parts.join(" · ")
}

// AR / LA legend only when the visible list has rows that show those buttons
const showActionLegend = computed(() =>
	visibleCategories.value.some((category) => category.key !== "no_issues")
)

function openAttendance(item) {
	if (!item.attendance) return
	window.open(`/app/attendance/${encodeURIComponent(item.attendance)}`, "_blank")
}

function handleDateClick(date) {
	selectedDate.value = date
	// reset per-date state
	activeDayTab.value = "issues"
	showDayDialog.value = true
}

function raiseRequest(doctype, employee, item) {
	const date = selectedDate.value.format("YYYY-MM-DD")
	let url = `/app/${doctype}/new?employee=${employee}&from_date=${date}&to_date=${date}`
	if (doctype === "attendance-request" && item?.hours_difference) {
		url += `&custom_hours_requested=${item.hours_difference}`
	}
	window.open(url, "_blank")
}

watch(
	() => cursorMonth.value,
	() => teamCalendar.fetch()
)

const getFirstLetter = (s) => Array.from(s.trim())[0] // Unicode

const DAYS = [
	getFirstLetter(__("Sunday")),
	getFirstLetter(__("Monday")),
	getFirstLetter(__("Tuesday")),
	getFirstLetter(__("Wednesday")),
	getFirstLetter(__("Thursday")),
	getFirstLetter(__("Friday")),
	getFirstLetter(__("Saturday")),
]

const teamCalendar = createResource({
	url: "craft_hr.api.get_team_attendance_calendar_details",
	auto: true,
	makeParams() {
		return {
			from_date: periodStart.value.format("YYYY-MM-DD"),
			to_date: periodEnd.value.format("YYYY-MM-DD"),
		}
	},
})

// "Checked" dates: a personal progress marker, saved per user
const checkedDates = ref([])

watch(
	() => teamCalendar.data?.checked_dates,
	(dates) => {
		// keep ticks from other months already loaded, replace this period's
		const start = periodStart.value.format("YYYY-MM-DD")
		const end = periodEnd.value.format("YYYY-MM-DD")
		const others = checkedDates.value.filter((d) => d < start || d > end)
		checkedDates.value = [...others, ...(dates || [])]
	},
	{ immediate: true }
)

function isChecked(date) {
	return !!date && checkedDates.value.includes(date.format("YYYY-MM-DD"))
}

const saveChecked = createResource({
	url: "craft_hr.api.set_team_calendar_date_checked",
})

function toggleChecked(checked) {
	if (!selectedDate.value) return
	const key = selectedDate.value.format("YYYY-MM-DD")
	const previous = [...checkedDates.value]
	// optimistic update, rolled back if saving fails
	checkedDates.value = checked
		? [...previous.filter((d) => d !== key), key]
		: previous.filter((d) => d !== key)
	saveChecked.submit(
		{ date: key, checked: checked ? 1 : 0 },
		{
			onError() {
				checkedDates.value = previous
			},
		}
	)
}
</script>
