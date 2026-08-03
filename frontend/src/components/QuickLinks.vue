<template>
	<div class="flex flex-col gap-5 my-4 w-full">
		<div class="text-lg font-semibold text-gray-900">{{ title || __("Quick Links") }}</div>
		<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
			<component
				:is="link.href ? 'a' : 'router-link'"
				class="flex flex-col items-center justify-center gap-3 bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md hover:border-gray-300 transition-shadow"
				v-for="link in props.items"
				:key="link.title"
				v-bind="link.href ? { href: link.href } : { to: { name: link.route } }"
			>
				<div class="flex items-center justify-center h-12 w-12 rounded-full bg-gray-100">
					<component :is="link.icon" class="h-6 w-6 text-gray-700" />
				</div>
				<div class="text-sm font-medium text-gray-800 text-center">
					{{ link.title }}
				</div>
			</component>
		</div>
	</div>
</template>

<script setup>
import { inject } from "vue"

const __ = inject("$translate")

const props = defineProps({
	title: {
		type: String,
		required: false,
		default: "",
	},
	items: {
		type: Array,
		required: true,
	},
})
</script>
