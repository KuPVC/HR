<template>
	<router-view v-slot="{ Component, route }">
		<component :is="Component" :key="route.fullPath" />
	</router-view>
	<Toasts />
</template>

<script setup>
import { Toasts } from "frappe-ui"
</script>
