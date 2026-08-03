const routes = [
	{
		name: "MaterialRequestListView",
		path: "/material-requests",
		component: () => import("@/views/material_request/List.vue"),
	},
]

export default routes
