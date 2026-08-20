<template>
	<div class="flex flex-col w-full gap-5" v-if="calendarEvents.data">
		<div class="text-lg text-gray-800 font-bold">
			{{ __("Attendance Calendar") }}
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
						class="relative h-9 w-9 mx-auto block"
						:class="hasInfo(cellDate) ? 'cursor-pointer' : 'cursor-default'"
						:disabled="!hasInfo(cellDate)"
						@click="handleDateClick(cellDate)"
					>
						<div
							class="h-8 w-8 flex rounded-full mx-auto"
							:class="[
								statusClass(cellDate),
								isCarryOver(cellDate) ? 'opacity-40' : '',
								isHighlighted(cellDate)
									? 'animate-pulse ring-2 ring-offset-1 ' + highlightRingClass
									: '',
							]"
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
						<div
							v-if="hasFlags(cellDate)"
							class="absolute -bottom-0.5 left-1/2 -translate-x-1/2 flex flex-row gap-0.5"
						>
							<span
								v-if="getFlags(cellDate).late_entry"
								class="h-1.5 w-1.5 rounded-full bg-amber-500"
								:title="__('Late Entry')"
							/>
							<span
								v-if="getFlags(cellDate).short_hours"
								class="h-1.5 w-1.5 rounded-full bg-purple-600"
								:title="__('Short Hours')"
							/>
							<span
								v-if="getFlags(cellDate).missed_punch"
								class="h-1.5 w-1.5 rounded-full bg-pink-600"
								:title="__('Missed Punch')"
							/>
						</div>
					</button>
				</div>
			</div>

			<hr />

			<!-- Summary Cards -->
			<div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
				<button
					type="button"
					v-for="card in summaryCards"
					:key="card.key"
					class="flex flex-col gap-1.5 rounded-lg border p-3 text-left transition-shadow"
					:class="[
						card.bg,
						card.border,
						isActiveFilter(card.type, card.value)
							? 'ring-2 ring-offset-1 ' + card.ring
							: 'hover:shadow-sm',
					]"
					@click="toggleFilter(card.type, card.value)"
				>
					<div class="flex flex-row gap-1.5 items-center">
						<span class="rounded-full h-2.5 w-2.5 shrink-0" :class="card.dot" />
						<span class="text-xs font-medium leading-4" :class="card.textMuted">
							{{ card.label }}
						</span>
					</div>
					<span
						class="text-xl font-semibold leading-6"
						:class="card.textStrong"
					>
						{{ card.count }}
					</span>
				</button>
			</div>
		</div>

		<div class="flex flex-row items-center gap-1.5 px-1 text-xs text-gray-500">
			<FeatherIcon name="info" class="h-3.5 w-3.5 shrink-0" />
			<span>{{
				__("Tip: click on a date to see check-in details or raise a request.")
			}}</span>
		</div>

		<Dialog v-model="showInfoDialog" :options="{ title: selectedDateLabel }">
			<template #body-content>
				<div class="flex flex-col gap-4">
					<div class="flex flex-col gap-1">
						<div class="text-sm text-gray-500">{{ __("Status") }}</div>
						<div class="text-base font-medium text-gray-800">
							{{ __(selectedEvent?.status || "No Record") }}
						</div>
					</div>

					<div v-if="dayCheckins.data?.length" class="flex flex-col gap-2">
						<div class="text-sm text-gray-500">{{ __("Check-in Logs") }}</div>
						<div class="flex flex-row flex-wrap gap-2">
							<Badge
								v-for="checkin in dayCheckins.data"
								:key="checkin.name"
								variant="subtle"
								:theme="checkin.attendance ? 'green' : 'gray'"
								size="md"
								:label="`${checkin.log_type} · ${dayjs(checkin.time).format(
									'h:mm A'
								)}`"
							/>
						</div>
						<div class="text-xs text-gray-500">
							{{
								__("Green indicates the log used for this day's attendance.")
							}}
						</div>
					</div>

					<div
						v-if="selectedEvent?.short_hours"
						class="text-sm text-purple-700"
					>
						{{
							__("Short by {0}", [
								formatHoursDuration(selectedEvent.hours_difference),
							])
						}}
					</div>
					<div v-if="selectedEvent?.late_entry" class="text-sm text-amber-700">
						{{ __("Late Entry") }}
					</div>
					<div v-if="selectedEvent?.missed_punch" class="text-sm text-pink-700">
						{{ __("Missed Punch") }}
					</div>

					<div
						v-if="selectedDate && isActionable(selectedDate)"
						class="flex flex-col gap-2 pt-3 border-t"
					>
						<div class="text-sm text-gray-500">
							{{ __("Need to raise a request for this date?") }}
						</div>
						<Button
							variant="solid"
							class="w-full"
							@click="goToAttendanceRequest"
						>
							{{ __("Attendance Request") }}
						</Button>
						<Button
							v-if="selectedEvent?.status === 'Absent'"
							variant="outline"
							class="w-full"
							@click="goToLeaveApplication"
						>
							{{ __("Leave Application") }}
						</Button>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Badge, Dialog, FeatherIcon, createResource } from "frappe-ui"

import { formatHoursDuration } from "@/utils/formatters"

const dayjs = inject("$dayjs")
const __ = inject("$translate")
const router = useRouter()

// cursorMonth anchors the payroll period: period runs from the 25th of the
// previous month through the 24th of cursorMonth (matches sj_hr's
// "Monthly-25" Monthly Attendance Sheet period).
const cursorMonth = ref(dayjs().date(1).startOf("D"))
const today = dayjs().startOf("day")

const periodEnd = computed(() => cursorMonth.value.endOf("month"))
const periodStart = computed(() => cursorMonth.value.subtract(1, "M").date(25))

const colorMap = {
	Present: "bg-green-300",
	"Work From Home": "bg-green-300",
	"Half Day": "bg-yellow-200",
	Absent: "bg-red-200",
	"On Leave": "bg-blue-300",
	Holiday: "bg-gray-300",
}

const ringClassByFlag = {
	late_entry: "ring-amber-500",
	short_hours: "ring-purple-600",
	missed_punch: "ring-pink-600",
}
const ringClassByStatus = {
	Present: "ring-green-500",
	"Half Day": "ring-yellow-500",
	Absent: "ring-red-500",
	"On Leave": "ring-blue-500",
}

// __("Present"), __("Half Day"), __("Absent"), __("On Leave"), __("Work From Home")
const summaryStatuses = ["Present", "Half Day", "Absent", "On Leave"]

const CARD_STYLES = {
	Present: {
		bg: "bg-green-50",
		border: "border-green-100",
		dot: "bg-green-400",
		textMuted: "text-green-700",
		textStrong: "text-green-800",
		ring: "ring-green-400",
	},
	"Half Day": {
		bg: "bg-yellow-50",
		border: "border-yellow-100",
		dot: "bg-yellow-400",
		textMuted: "text-yellow-700",
		textStrong: "text-yellow-800",
		ring: "ring-yellow-400",
	},
	Absent: {
		bg: "bg-red-50",
		border: "border-red-100",
		dot: "bg-red-400",
		textMuted: "text-red-700",
		textStrong: "text-red-800",
		ring: "ring-red-400",
	},
	"On Leave": {
		bg: "bg-blue-50",
		border: "border-blue-100",
		dot: "bg-blue-400",
		textMuted: "text-blue-700",
		textStrong: "text-blue-800",
		ring: "ring-blue-400",
	},
	late_entry: {
		bg: "bg-amber-50",
		border: "border-amber-100",
		dot: "bg-amber-500",
		textMuted: "text-amber-700",
		textStrong: "text-amber-800",
		ring: "ring-amber-500",
	},
	short_hours: {
		bg: "bg-purple-50",
		border: "border-purple-100",
		dot: "bg-purple-600",
		textMuted: "text-purple-700",
		textStrong: "text-purple-800",
		ring: "ring-purple-600",
	},
	missed_punch: {
		bg: "bg-pink-50",
		border: "border-pink-100",
		dot: "bg-pink-600",
		textMuted: "text-pink-700",
		textStrong: "text-pink-800",
		ring: "ring-pink-600",
	},
}

const FLAG_LABELS = {
	late_entry: "Late Entry",
	short_hours: "Short Hours",
	missed_punch: "Missed Punch",
}

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
	// days still belonging to the previous calendar month, shown faded
	return date.isBefore(cursorMonth.value, "day")
}

function isToday(date) {
	return date.isSame(today, "day")
}

function getEventOnDate(date) {
	return calendarEvents.data?.[date.format("YYYY-MM-DD")]
}

function statusClass(date) {
	const event = getEventOnDate(date)
	return event?.status ? colorMap[event.status] : ""
}

function getFlags(date) {
	return getEventOnDate(date) || {}
}

function hasFlags(date) {
	const flags = getFlags(date)
	return !!(flags.late_entry || flags.short_hours || flags.missed_punch)
}

// a date needs an Attendance Request (or, for Absent days, either an
// Attendance Request or a Leave Application) when there's no record for it
// yet (and it isn't a holiday/future date), the day is marked Absent, or the
// recorded day is flagged with late entry / short hours / missed punch.
function isActionable(date) {
	if (date.isAfter(today, "day")) return false

	const event = getEventOnDate(date)
	if (!event) return true
	if (event.status === "Holiday" || event.status === "On Leave") return false
	if (event.status === "Absent") return true

	return !!(event.late_entry || event.short_hours || event.missed_punch)
}

// a date is worth opening the info dialog for when there's an Attendance
// event to show (check-in/out, flags) or it's actionable (missing record).
function hasInfo(date) {
	if (date.isAfter(today, "day")) return false
	return !!getEventOnDate(date) || isActionable(date)
}

const showInfoDialog = ref(false)
const selectedDate = ref(null)
const selectedEvent = computed(() =>
	selectedDate.value ? getEventOnDate(selectedDate.value) : null
)
const selectedDateLabel = computed(() =>
	selectedDate.value ? selectedDate.value.format("D MMMM YYYY") : ""
)

const dayCheckins = createResource({
	url: "craft_hr.api.get_checkins_for_period",
	auto: false,
})

function handleDateClick(date) {
	if (!hasInfo(date)) return
	selectedDate.value = date
	showInfoDialog.value = true

	const dateStr = date.format("YYYY-MM-DD")
	dayCheckins.fetch({ from_date: dateStr, to_date: dateStr })
}

function goToAttendanceRequest() {
	showInfoDialog.value = false
	const event = selectedEvent.value
	const query = { date: selectedDate.value.format("YYYY-MM-DD") }
	if (event?.short_hours && event.hours_difference) {
		query.hours = event.hours_difference
	}
	router.push({ name: "AttendanceRequestFormView", query })
}

function goToLeaveApplication() {
	showInfoDialog.value = false
	router.push({
		name: "LeaveApplicationFormView",
		query: { date: selectedDate.value.format("YYYY-MM-DD") },
	})
}

const activeFilter = ref(null) // { type: 'status' | 'flag', value: string }

function toggleFilter(type, value) {
	if (
		activeFilter.value?.type === type &&
		activeFilter.value?.value === value
	) {
		activeFilter.value = null
	} else {
		activeFilter.value = { type, value }
	}
}

function isActiveFilter(type, value) {
	return (
		activeFilter.value?.type === type && activeFilter.value?.value === value
	)
}

function isHighlighted(date) {
	if (!activeFilter.value) return false
	const event = getEventOnDate(date)
	if (!event) return false

	if (activeFilter.value.type === "status") {
		const status = event.status === "Work From Home" ? "Present" : event.status
		return status === activeFilter.value.value
	}
	return !!event[activeFilter.value.value]
}

const highlightRingClass = computed(() => {
	if (!activeFilter.value) return ""
	return activeFilter.value.type === "flag"
		? ringClassByFlag[activeFilter.value.value]
		: ringClassByStatus[activeFilter.value.value]
})

const summary = computed(() => {
	const summary = {}

	for (const event of Object.values(calendarEvents.data || {})) {
		let updatedStatus =
			event.status === "Work From Home" ? "Present" : event.status
		if (!updatedStatus) continue
		summary[updatedStatus] = (summary[updatedStatus] || 0) + 1
	}

	return summary
})

const flagSummary = computed(() => {
	const totals = { late_entry: 0, short_hours: 0, missed_punch: 0 }
	for (const event of Object.values(calendarEvents.data || {})) {
		if (event.late_entry) totals.late_entry += 1
		if (event.short_hours) totals.short_hours += 1
		if (event.missed_punch) totals.missed_punch += 1
	}
	return totals
})

const summaryCards = computed(() => [
	...summaryStatuses.map((status) => ({
		key: `status-${status}`,
		type: "status",
		value: status,
		label: __(status),
		count: summary.value[status] || 0,
		...CARD_STYLES[status],
	})),
	...Object.keys(flagSummary.value).map((flag) => ({
		key: `flag-${flag}`,
		type: "flag",
		value: flag,
		label: __(FLAG_LABELS[flag]),
		count: flagSummary.value[flag],
		...CARD_STYLES[flag],
	})),
])

watch(
	() => cursorMonth.value,
	() => {
		activeFilter.value = null
		calendarEvents.fetch()
	}
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

//resources
const calendarEvents = createResource({
	url: "craft_hr.api.get_attendance_calendar_details",
	auto: true,
	makeParams() {
		return {
			from_date: periodStart.value.format("YYYY-MM-DD"),
			to_date: periodEnd.value.format("YYYY-MM-DD"),
		}
	},
})
</script>
