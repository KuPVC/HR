<template>
	<div class="flex flex-col gap-3 py-4">
		<h2 class="text-base font-semibold text-gray-800">{{ __("Comments") }}</h2>

		<div v-if="comments.data?.length" class="flex flex-col gap-4">
			<div
				v-for="comment in comments.data"
				:key="comment.name"
				class="flex flex-row items-start gap-2"
			>
				<Avatar :label="comment.comment_by" size="sm" />
				<div class="flex flex-col gap-0.5 bg-gray-100 rounded p-2 grow">
					<div class="flex flex-row items-center justify-between gap-2">
						<span class="text-sm font-medium text-gray-800">{{ comment.comment_by }}</span>
						<span class="text-xs text-gray-500 whitespace-nowrap">
							{{ formatTimestamp(comment.creation) }}
						</span>
					</div>
					<div class="text-sm text-gray-700 comment-content" v-html="comment.content"></div>
				</div>
			</div>
		</div>

		<div v-else-if="comments.loading" class="text-sm text-gray-500">
			{{ __("Loading comments...") }}
		</div>

		<div class="flex flex-row items-start gap-2">
			<FormControl
				type="textarea"
				class="grow"
				:placeholder="__('Add a comment')"
				v-model="newComment"
				:disabled="addComment.loading"
			/>
			<Button
				variant="solid"
				:disabled="!newComment?.trim()"
				:loading="addComment.loading"
				@click="submitComment"
			>
				{{ __("Send") }}
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref, inject } from "vue"
import { Avatar, FormControl, createResource } from "frappe-ui"

import { formatTimestamp } from "@/utils/formatters"

const __ = inject("$translate")
const user = inject("$user")

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	docname: {
		type: String,
		required: true,
	},
})

const newComment = ref("")

const comments = createResource({
	url: "craft_hr.api.get_comments",
	params: {
		reference_doctype: props.doctype,
		reference_name: props.docname,
	},
	auto: true,
})

const addComment = createResource({
	url: "frappe.desk.form.utils.add_comment",
	makeParams() {
		return {
			reference_doctype: props.doctype,
			reference_name: props.docname,
			content: newComment.value,
			comment_email: user.data?.name,
			comment_by: user.data?.full_name,
		}
	},
	onSuccess() {
		newComment.value = ""
		comments.reload()
	},
})

function submitComment() {
	if (!newComment.value?.trim()) return
	addComment.submit()
}
</script>

<style scoped>
.comment-content :deep(p) {
	margin: 0;
}
</style>
