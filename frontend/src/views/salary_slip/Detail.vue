<template>
	<AppShell :pageTitle="__('Salary Slip')">
		<template #body>
			<div class="flex flex-col gap-4">
				<div class="flex flex-row items-center justify-between">
					<ErrorMessage :message="downloadError" />
					<Button
						class="ml-auto"
						variant="solid"
						:loading="loading"
						@click="downloadPDF"
					>
						<template #prefix>
							<FeatherIcon name="download" class="h-4 w-4" />
						</template>
						{{ __("Download PDF") }}
					</Button>
				</div>

				<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-2 md:p-4">
					<iframe
						:src="printViewUrl"
						class="w-full border-0 rounded-lg"
						style="height: 80vh"
						title="Salary Slip Print View"
					/>
				</div>
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { ref, computed } from "vue"

import { Button, ErrorMessage, FeatherIcon } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"
import { downloadDoctypePdf } from "@/utils/downloadPdf"

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

const downloadError = ref("")
const loading = ref(false)

const printViewUrl = computed(() => {
	const params = new URLSearchParams({
		doctype: "Salary Slip",
		name: props.id,
		trigger_print: "0",
	})
	return `/printview?${params.toString()}`
})

function downloadPDF() {
	loading.value = true
	downloadDoctypePdf("Salary Slip", props.id)
		.catch((error) => {
			downloadError.value = `Failed to download PDF: ${error.message}`
		})
		.finally(() => {
			loading.value = false
		})
}
</script>
