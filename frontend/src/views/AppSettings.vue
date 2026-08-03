<template>
	<AppShell :pageTitle="__('Settings')">
		<template #body>
			<div class="flex flex-col gap-5 w-full max-w-2xl">
				<div class="flex flex-col bg-white rounded">
					<div
						class="flex flex-row cursor-pointer flex-start p-4 items-center justify-between border-b"
					>
						<router-link
							:to="{ name: 'ChangePassword' }"
							class="flex flex-row items-center justify-between w-full"
						>
							<div class="flex flex-row items-center gap-3 grow">
								<FeatherIcon
									name="lock"
									class="h-5 w-5 text-gray-500"
								/>
								<div class="text-base font-normal text-gray-800">
									{{ __("Change Password") }}
								</div>
							</div>
							<FeatherIcon
								name="chevron-right"
								class="h-5 w-5 text-gray-500"
							/>
						</router-link>
					</div>
				</div>
			</div>
		</template>
	</AppShell>
</template>

<script setup>
import { inject } from "vue"
import { FeatherIcon } from "frappe-ui"

import AppShell from "@/components/AppShell.vue"

const __ = inject("$translate")
</script>
