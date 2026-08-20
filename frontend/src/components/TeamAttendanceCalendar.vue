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
						class="relative h-9 w-9 mx-auto block"
						:class="
							isActionable(cellDate) ? 'cursor-pointer' : 'cursor-default'
						"
						:disabled="!isActionable(cellDate)"
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
					</button>
				</div>
			</div>
		</div>

		<div class="flex flex-row items-center gap-1.5 px-1 text-xs text-gray-500">
			<FeatherIcon name="info" class="h-3.5 w-3.5 shrink-0" />
			<span>{{
				__("Tip: click on a highlighted date to review who needs attention.")
			}}</span>
		</div>

		<Dialog
			v-model="showDayDialog"
			:options="{ title: selectedDateLabel, size: 'lg' }"
		>
			<template #body-content>
				<div v-if="dayCategories.length" class="flex flex-col gap-5">
					<div
						v-for="category in dayCategories"
						:key="category.key"
						class="flex flex-col gap-2"
					>
						<div class="text-sm font-semibold text-gray-700">
							{{ category.label }} ({{ category.items.length }})
						</div>
						<div
							v-for="item in category.items"
							:key="`${category.key}-${item.employee}`"
							class="flex flex-col gap-2 rounded-lg border border-gray-100 p-2.5"
						>
							<div class="flex flex-row items-center justify-between gap-3">
								<EmployeeAvatar :employeeID="item.employee" showLabel />
								<div class="flex flex-row gap-2 shrink-0">
									<Button
										v-if="category.key === 'absent'"
										variant="outline"
										@click="
											raiseRequest('leave-application', item.employee, item)
										"
									>
										{{ __("Leave Application") }}
									</Button>
									<Button
										variant="outline"
										@click="
											raiseRequest('attendance-request', item.employee, item)
										"
									>
										{{ __("Attendance Request") }}
									</Button>
								</div>
							</div>
							<div
								v-if="item.in_time || item.out_time || item.hours_difference"
								class="flex flex-row gap-4 pl-11 text-xs text-gray-500"
							>
								<span v-if="item.in_time || item.out_time">
									{{ __("In") }}:
									{{
										item.in_time ? dayjs(item.in_time).format("h:mm A") : "-"
									}}
									&middot;
									{{ __("Out") }}:
									{{
										item.out_time ? dayjs(item.out_time).format("h:mm A") : "-"
									}}
								</span>
								<span v-if="item.hours_difference" class="text-purple-700">
									{{
										__("Short by {0}", [
											formatHoursDuration(item.hours_difference),
										])
									}}
								</span>
							</div>
						</div>
					</div>
				</div>
				<EmptyState v-else :message="__('Nothing to review for this date')" />
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { Button, Dialog, FeatherIcon, createResource } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
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

function isActionable(date) {
	if (date.isAfter(today, "day")) return false
	return !!getDay(date)
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

const dayCategories = computed(() => {
	const day = selectedDate.value ? getDay(selectedDate.value) : null
	if (!day) return []

	return Object.keys(CATEGORY_LABELS)
		.map((key) => ({
			key,
			label: __(CATEGORY_LABELS[key]),
			items: day[key] || [],
		}))
		.filter((category) => category.items.length)
})

function handleDateClick(date) {
	if (!isActionable(date)) return
	selectedDate.value = date
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
</script>
