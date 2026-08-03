import { toast } from "frappe-ui"

export const showErrorAlert = async (message) => {
	toast({
		title: "Error",
		text: message,
		icon: "alert-circle",
		position: "bottom-center",
		iconClasses: "text-red-500",
	})
}
