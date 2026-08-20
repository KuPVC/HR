import { createResource } from "frappe-ui"

const transformOvertimeSlips = (data) =>
	data.map((slip) => {
		slip.doctype = "Overtime Slip"
		return slip
	})

export const teamOvertimeSlips = createResource({
	url: "craft_hr.api.get_team_overtime_slips",
	params: {
		limit: 10,
	},
	auto: true,
	cache: "craft_hr:team_overtime_slips",
	transform(data) {
		return transformOvertimeSlips(data)
	},
})
