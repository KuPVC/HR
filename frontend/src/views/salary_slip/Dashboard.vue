<template>
	<AppShell :pageTitle="__('Salary Slips')">
		<template #body>
			<div class="flex flex-col w-full max-w-[1600px] mx-auto">
				<div class="flex flex-col w-full bg-white rounded-xl border border-gray-200 shadow-sm py-5 px-4 gap-5">
					<div v-if="lastSalarySlip && lastSalarySlip.year_to_date" class="flex flex-col w-full gap-1.5">
						<span class="text-gray-500 text-sm font-medium leading-5">
							{{ __("Year To Date") }}
						</span>
						<span class="text-gray-900 text-xl font-semibold leading-6">
							{{
								formatCurrency(
									lastSalarySlip.year_to_date,
									lastSalarySlip.currency
								)
							}}
						</span>
					</div>

					<Autocomplete
						:label="__('Payroll Period')"
						class="w-full max-w-sm"
						:placeholder="__('Select Payroll Period')"
						v-model="selectedPeriod"
						:options="periodOptions"
					/>
				</div>

				<div class="flex flex-col items-center mt-5 mb-7 w-full">
					<div
						v-if="documents.data?.length"
						class="flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm overflow-auto w-full"
					>
						<div
							class="p-3.5 items-center justify-between border-b border-gray-100 last:border-b-0 cursor-pointer"
							v-for="link in documents.data"
							:key="link.name"
						>
							<SalarySlipItem
								:doc="link"
								:loading="downloadingName === link.name"
								@click="handleSelect(link)"
							/>
						</div>
					</div>
					<EmptyState :message="__('No salary slips found')" v-else />
				</div>
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { inject, ref, computed, watch, onMounted, onBeforeUnmount } from "vue"
import { useRouter } from "vue-router"
import { Autocomplete, createListResource, toast } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import EmptyState from "@/components/EmptyState.vue"
import SalarySlipItem from "@/components/SalarySlipItem.vue"

import { formatCurrency } from "@/utils/formatters"
import { downloadDoctypePdf } from "@/utils/downloadPdf"

const router = useRouter()
const MOBILE_BREAKPOINT_QUERY = "(max-width: 767px)"
const downloadingName = ref("")

function handleSelect(doc) {
	const isMobile = window.matchMedia(MOBILE_BREAKPOINT_QUERY).matches
	if (isMobile) {
		if (downloadingName.value) return

		downloadingName.value = doc.name
		toast({
			title: __("Downloading"),
			text: __("Preparing {0}, this may take a few seconds…", [doc.name]),
			icon: "download",
			position: "bottom-center",
			iconClasses: "text-gray-700",
		})

		downloadDoctypePdf("Salary Slip", doc.name)
			.catch(() => {
				toast({
					title: __("Error"),
					text: __("Failed to download PDF"),
					icon: "x-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			})
			.finally(() => {
				downloadingName.value = ""
			})
		return
	}
	router.push({ name: "SalarySlipDetailView", params: { id: doc.name } })
}

const ALL_PERIODS = { label: "", value: "__all__" }

let selectedPeriod = ref(ALL_PERIODS)
let periodsByName = ref({})

const employee = inject("$employee")
const dayjs = inject("$dayjs")
const socket = inject("$socket")
const __ = inject("$translate")

ALL_PERIODS.label = __("All Periods")

const payrollPeriods = createListResource({
	doctype: "Payroll Period",
	fields: ["name", "start_date", "end_date"],
	filters: {
		company: employee.data?.company,
	},
	orderBy: "start_date desc",
	auto: true,
	transform(data) {
		return data.map((period) => {
			periodsByName.value[period.name] = period
			return {
				label: getPeriodLabel(period),
				value: period.name,
			}
		})
	},
})

const periodOptions = computed(() => [ALL_PERIODS, ...(payrollPeriods.data || [])])

const documents = createListResource({
	doctype: "Salary Slip",
	fields: [
		"name",
		"start_date",
		"end_date",
		"currency",
		"gross_pay",
		"net_pay",
		"year_to_date",
	],
	filters: {
		employee: employee.data?.name,
		docstatus: 1,
	},
	orderBy: "posting_date desc",
	auto: true,
})

const lastSalarySlip = computed(() => documents.data?.[0])

function getPeriodLabel(period) {
	return `${dayjs(period?.start_date).format("MMM YYYY")} - ${dayjs(
		period?.end_date
	).format("MMM YYYY")}`
}

watch(
	() => selectedPeriod.value,
	(value) => {
		if (!value || value.value === "__all__") {
			delete documents.filters.start_date
			documents.reload()
			return
		}

		let period = periodsByName.value[value?.value]
		if (!period) return

		documents.filters.start_date = [
			"between",
			[period.start_date, period.end_date],
		]
		documents.reload()
	}
)

onMounted(() => {
	socket.on("hrms:update_salary_slips", (data) => {
		if (data.employee === employee.data.name) {
			documents.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_salary_slips")
})
</script>
