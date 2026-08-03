<template>
	<div
		v-if="actions.length > 0"
		:class="[
			props.view === 'form'
				? 'px-4 pt-4 pb-4 bg-white sticky bottom-0 w-full drop-shadow-xl z-40 border-t rounded-t-lg'
				: 'flex w-full flex-row flex-wrap items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4',
		]"
	>
		<Button
			v-for="action in actions"
			:key="action.text"
			class="w-full py-5"
			:variant="action.variant"
			:theme="action.theme"
			@click="applyWorkflow(action)"
		>
			<template #prefix v-if="action.featherIcon">
				<FeatherIcon :name="action.featherIcon" class="w-4" />
			</template>
			{{ __(action.text, null, props.doc?.doctype) }}
		</Button>
	</div>
</template>

<script setup>
import { ref, onMounted, inject } from "vue"
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
	doc: {
		type: Object,
		required: true,
	},
	workflow: {
		type: Object,
		required: false,
	},
	view: {
		type: String,
		default: "form",
		validator: (value) => ["form", "actionSheet"].includes(value),
	},
})

const emit = defineEmits(["workflow-applied"])

const __ = inject("$translate")
let actions = ref([])

const getTransitions = async () => {
	const transitions = await props.workflow.getTransitions(props.doc)
	actions.value = transitions.map((transition) => {
		let theme = "gray"
		let variant = "subtle"
		let icon = ""
		let actionLabel = transition.toLowerCase()

		if (actionLabel.includes("reject") || actionLabel.includes("cancel")) {
			theme = "red"
			variant = "subtle"
			icon = "x"
		} else if (actionLabel.includes("approve")) {
			theme = "green"
			variant = "solid"
			icon = "check"
		}

		return {
			text: __(transition, null, props.doc?.doctype),
			theme: theme,
			variant: variant,
			featherIcon: icon,
			action: transition,
		}
	})
}

const applyWorkflow = async (action) => {
	await props.workflow.applyWorkflow(props.doc, action.action)
	emit("workflow-applied")
}

onMounted(() => getTransitions())
</script>
