<template>
	<div class="flex flex-col gap-3 py-4 w-full">
		<h2 class="text-base font-semibold text-gray-800">{{ __("Comments") }}</h2>

		<div v-if="comments.data?.length" class="flex flex-col gap-4 w-full">
			<div
				v-for="comment in comments.data"
				:key="comment.name"
				class="flex flex-row items-start gap-2"
			>
				<Avatar :label="comment.comment_by" size="sm" />
				<div class="flex flex-col gap-0.5 bg-gray-100 rounded p-2 grow">
					<div class="flex flex-row items-center justify-between gap-2">
						<span class="text-sm font-medium text-gray-800">{{
							comment.comment_by
						}}</span>
						<span class="text-xs text-gray-500 whitespace-nowrap">
							{{ formatTimestamp(comment.creation) }}
						</span>
					</div>
					<div
						class="text-sm text-gray-700 comment-content"
						v-html="comment.content"
					></div>
				</div>
			</div>
		</div>

		<div v-else-if="comments.loading" class="text-sm text-gray-500">
			{{ __("Loading comments...") }}
		</div>

		<div class="flex flex-col items-end gap-2">
			<TextEditor
				v-if="mentions.data"
				ref="editor"
				class="w-full comment-editor"
				editor-class="prose-sm max-w-none min-h-[3rem] px-3 py-2 border-x border-b rounded-b-lg"
				:placeholder="__('Add a comment')"
				:content="newComment"
				:mentions="mentionOptions"
				:fixed-menu="fixedMenuButtons"
				:bubble-menu="true"
				:editable="!addComment.loading"
				@change="(val) => (newComment = val)"
			/>
			<FormControl
				v-else
				type="textarea"
				class="w-full"
				:placeholder="__('Add a comment')"
				disabled
			/>
			<Button
				variant="solid"
				:disabled="!hasContent"
				:loading="addComment.loading"
				@click="submitComment"
			>
				{{ __("Send") }}
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject } from "vue"
import {
	Avatar,
	Button,
	FormControl,
	TextEditor,
	createResource,
} from "frappe-ui"

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
const editor = ref(null)

const fixedMenuButtons = [
	"Bold",
	"Italic",
	"Separator",
	"Bullet List",
	"Numbered List",
	"Separator",
	"Link",
	"Blockquote",
	"Code",
	"Separator",
	"Undo",
	"Redo",
]

const comments = createResource({
	url: "craft_hr.api.get_comments",
	params: {
		reference_doctype: props.doctype,
		reference_name: props.docname,
	},
	auto: true,
})

// Same endpoint the desk comment box uses for @mention suggestions, so
// mentions here resolve to the same users/user groups and produce the
// `<span class="mention" data-id="...">` markup that
// frappe.desk.notifications.extract_mentions expects.
const mentions = createResource({
	url: "frappe.desk.search.get_names_for_mentions",
	params: { search_term: "" },
	auto: true,
})

const mentionOptions = computed(() =>
	(mentions.data || []).map((m) => ({ label: m.value, value: m.id }))
)

const hasContent = computed(() => {
	const text = newComment.value?.replace(/<[^>]*>/g, "").trim()
	return !!text
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
		editor.value?.editor?.commands.clearContent(true)
		comments.reload()
	},
})

function submitComment() {
	if (!hasContent.value) return
	addComment.submit()
}
</script>

<style scoped>
.comment-content :deep(p) {
	margin: 0;
}

.comment-editor :deep(.mention) {
	color: var(--blue-600, #2563eb);
}
</style>
