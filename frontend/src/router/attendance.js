const routes = [
	{
		name: "AttendanceRequestListView",
		path: "/attendance-requests",
		component: () => import("@/views/attendance/AttendanceRequestList.vue"),
	},
	{
		name: "AttendanceRequestFormView",
		path: "/attendance-requests/new",
		component: () => import("@/views/attendance/AttendanceRequestForm.vue"),
	},
	{
		name: "AttendanceRequestDetailView",
		path: "/attendance-requests/:id",
		props: true,
		component: () => import("@/views/attendance/AttendanceRequestForm.vue"),
	},
]

export default routes
