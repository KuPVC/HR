export function downloadDoctypePdf(doctype, docname) {
	let headers = { "X-Frappe-Site-Name": window.location.hostname }
	if (window.csrf_token) {
		headers["X-Frappe-CSRF-Token"] = window.csrf_token
	}

	return fetch("/api/method/hrms.api._download_pdf", {
		method: "POST",
		headers,
		body: new URLSearchParams({ doctype, docname }),
	})
		.then((response) => {
			if (!response.ok) {
				throw new Error("Failed to download PDF")
			}
			return response.blob()
		})
		.then((blob) => {
			const blobUrl = window.URL.createObjectURL(blob)
			const link = document.createElement("a")
			link.href = blobUrl
			link.download = `${docname}.pdf`
			link.click()

			setTimeout(() => {
				window.URL.revokeObjectURL(blobUrl)
			}, 3000)
		})
}
