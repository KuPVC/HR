import { createRouter, createWebHistory } from "vue-router"

import attendanceRoutes from "./attendance"
import leaveRoutes from "./leaves"
import salarySlipRoutes from "./salary_slips"
import materialRequestRoutes from "./material_request"
import overtimeSlipRoutes from "./overtime_slip"

const routes = [
	{
		path: "/",
		redirect: "/home",
	},
	{
		path: "/home",
		name: "Home",
		component: () => import("@/views/Home.vue"),
	},
	{
		path: "/dashboard/attendance",
		name: "AttendanceDashboard",
		component: () => import("@/views/attendance/Dashboard.vue"),
	},
	{
		path: "/dashboard/leaves",
		name: "LeavesDashboard",
		component: () => import("@/views/leave/Dashboard.vue"),
	},
	{
		path: "/dashboard/salary-slips",
		name: "SalarySlipsDashboard",
		component: () => import("@/views/salary_slip/Dashboard.vue"),
	},
	{
		path: "/login",
		name: "Login",
		component: () => import("@/views/Login.vue"),
	},
	{
		path: "/forgot-password",
		name: "ForgotPassword",
		component: () => import("@/views/ForgotPassword.vue"),
	},
	{
		path: "/profile",
		name: "Profile",
		component: () => import("@/views/Profile.vue"),
	},
	{
		path: "/notifications",
		name: "Notifications",
		component: () => import("@/views/Notifications.vue"),
	},
	{
		path: "/settings",
		name: "Settings",
		component: () => import("@/views/AppSettings.vue"),
	},
	{
		path: "/change-password",
		name: "ChangePassword",
		component: () => import("@/views/ChangePassword.vue"),
	},
	{
		path: "/invalid-employee",
		name: "InvalidEmployee",
		component: () => import("@/views/InvalidEmployee.vue"),
	},
	...attendanceRoutes,
	...leaveRoutes,
	...salarySlipRoutes,
	...materialRequestRoutes,
	...overtimeSlipRoutes,
]

const router = createRouter({
	history: createWebHistory("/ess"),
	routes,
})

export default router
