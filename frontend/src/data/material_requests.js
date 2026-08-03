import { createListResource } from "frappe-ui"
import { userResource } from "./user"

const transformMaterialRequests = (data) =>
	data.map((request) => {
		request.doctype = "Material Request"
		return request
	})

export const myMaterialRequests = createListResource({
	doctype: "Material Request",
	fields: ["name", "transaction_date", "material_request_type", "status", "creation"],
	filters: {
		owner: userResource.data?.name,
	},
	orderBy: "creation desc",
	pageLength: 10,
	auto: true,
	cache: "craft_hr:my_material_requests",
	transform(data) {
		return transformMaterialRequests(data)
	},
})
