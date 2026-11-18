// Workflow State badge helpers (Workflow State "style" = Success / Danger /
// Warning / Primary / Info / Inverse).

const BADGE_CLASSES = {
	Success: "bg-green-100 text-green-700",
	Danger: "bg-red-100 text-red-700",
	Warning: "bg-orange-100 text-orange-700",
	Primary: "bg-blue-100 text-blue-700",
	Info: "bg-sky-100 text-sky-700",
	Inverse: "bg-gray-800 text-white",
}

const BADGE_THEMES = {
	Success: "green",
	Danger: "red",
	Warning: "orange",
	Primary: "blue",
	Info: "blue",
	Inverse: "gray",
}

// Docs without a workflow state fall back to their document status.
export function stateLabel(doc, __) {
	if (doc.workflow_state) return doc.workflow_state
	if (doc.docstatus === 2) return __("Cancelled")
	return doc.docstatus ? __("Submitted") : __("Draft")
}

export function stateClasses(doc) {
	if (doc.workflow_state && BADGE_CLASSES[doc.state_style])
		return BADGE_CLASSES[doc.state_style]
	if (doc.workflow_state) return "bg-gray-100 text-gray-700"
	if (doc.docstatus === 2) return "bg-red-100 text-red-700"
	return doc.docstatus ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
}

export function stateTheme(doc) {
	if (doc.workflow_state) return BADGE_THEMES[doc.state_style] || "gray"
	if (doc.docstatus === 2) return "red"
	return doc.docstatus ? "blue" : "gray"
}
