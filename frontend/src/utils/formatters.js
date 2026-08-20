import { createDocumentResource } from "frappe-ui"

import dayjs from "@/utils/dayjs"

const settings = createDocumentResource({
	doctype: "System Settings",
	name: "System Settings",
	auto: false,
})

export const formatCurrency = (value, currency) => {
	if (!currency) return value

	// hack: if value contains a space, it is already formatted
	if (value?.toString().trim().includes(" ")) return value

	const locale =
		settings.doc?.country == "India" ? "en-IN" : settings.doc?.language

	const formatter = Intl.NumberFormat(locale, {
		style: "currency",
		currency: currency,
		trailingZeroDisplay: "stripIfInteger",
		currencyDisplay: "narrowSymbol",
	})
	return (
		formatter
			.format(value)
			// add space between the digits and symbol
			.replace(/^(\D+)/, "$1 ")
			// remove extra spaces if any (added by some browsers)
			.replace(/\s+/, " ")
	)
}

// hoursDecimal (e.g. 1.4090) -> "1 hr 24 min 32 sec", dropping any leading
// zero units so a sub-minute gap reads as "43 sec" rather than "0 hr 0 min 43 sec"
export const formatHoursDuration = (hoursDecimal) => {
	const totalSeconds = Math.round(hoursDecimal * 3600)
	const hours = Math.floor(totalSeconds / 3600)
	const minutes = Math.floor((totalSeconds % 3600) / 60)
	const seconds = totalSeconds % 60

	const parts = []
	if (hours) parts.push(`${hours} hr`)
	if (minutes) parts.push(`${minutes} min`)
	if (seconds || !parts.length) parts.push(`${seconds} sec`)

	return parts.join(" ")
}

// inverse of formatHoursDuration - hoursDecimal -> {hours, minutes, seconds},
// used to pre-fill the hr/min/sec picker with whatever's already in the field
export const decomposeHoursDuration = (hoursDecimal) => {
	const totalSeconds = Math.round((hoursDecimal || 0) * 3600)
	return {
		hours: Math.floor(totalSeconds / 3600),
		minutes: Math.floor((totalSeconds % 3600) / 60),
		seconds: totalSeconds % 60,
	}
}

export const formatTimestamp = (timestamp) => {
	const formattedTime = dayjs(timestamp).format("hh:mm a")

	if (dayjs(timestamp).isToday()) return formattedTime
	else if (dayjs(timestamp).isYesterday()) return `${formattedTime} yesterday`
	else if (dayjs(timestamp).isSame(dayjs(), "year"))
		return `${formattedTime} on ${dayjs(timestamp).format("D MMM")}`

	return `${formattedTime} on ${dayjs(timestamp).format("D MMM, YYYY")}`
}
