<template>
	<div class="bg-white w-full flex flex-col">
		<div class="flex flex-row items-center justify-between border-b p-3">
			<span class="font-semibold text-gray-900">{{ filename }} - {{ __("File Preview") }}</span>
			<Button variant="ghost" @click="emit('close')">{{ __("Close") }}</Button>
		</div>
		<div class="bg-white h-[70vh] w-full overflow-auto touch-pinch-zoom">
			<img v-if="isImageFile" :src="src" class="h-auto image-preview max-w-full" />
			<iframe v-else :src="src" class="w-full h-full"></iframe>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount } from "vue"

const __ = inject("$translate")
const emit = defineEmits(["close"])

const props = defineProps({
	file: {
		type: Object,
		required: true,
	},
})

const filename = computed(() => {
	return props.file.file_name || props.file.name
})

const src = computed(() => {
	return props.file.file_url
		? props.file.file_url
		: URL.createObjectURL(props.file)
})

const isImageFile = computed(() => {
	return /\.(gif|jpg|jpeg|tiff|png|svg)$/i.test(filename.value)
})

onBeforeUnmount(() => {
	if (!props.file.file_url) URL.revokeObjectURL(src.value)
})
</script>

<style scoped>
.image-preview {
	image-orientation: from-image;
}
</style>
