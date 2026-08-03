<template>
	<AppShell :pageTitle="__('Leaves & Holidays')">
		<template #body>
			<div class="flex flex-col gap-7 w-full max-w-[1600px] mx-auto">
				<LeaveBalance />

				<div class="w-full max-w-xs">
					<router-link
						:to="{ name: 'LeaveApplicationFormView' }"
						v-slot="{ navigate }"
					>
						<Button
							@click="navigate"
							variant="solid"
							class="py-5 text-base w-full"
						>
							{{ __("Request a Leave") }}
						</Button>
					</router-link>
				</div>
				<div>
					<div class="text-lg text-gray-900 font-semibold">{{ __('Recent Leaves') }} </div>
					<RequestList
						:component="markRaw(LeaveRequestItem)"
						:items="myLeaves.data"
						:addListButton="true"
						listButtonRoute="LeaveApplicationListView"
					/>
				</div>
				<Holidays />
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { markRaw } from "vue"

import AppShell from "@/components/AppShell.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"
import RequestList from "@/components/RequestList.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import Holidays from "@/components/Holidays.vue"

import { myLeaves } from "@/data/leaves"
</script>
