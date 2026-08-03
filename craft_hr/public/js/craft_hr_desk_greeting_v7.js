// Adds a live greeting + date/time line above the app-icon grid on the Desk
// "Desktop" (apps) page ONLY — desktop viewports only, never inside a
// module/folder drill-down (e.g. Accounting) or any other workspace page.
frappe.provide("craft_hr");

// Frappe's desktop-icon palette only ships "blue" and "gray" — extend it so
// the Employee Self Service tile can stand out with its own color.
if (frappe.utils && frappe.utils.desktop_pallete && !frappe.utils.desktop_pallete.purple) {
	frappe.utils.desktop_pallete.purple = "#7C3AED";
}

// load the font immediately (script eval time), not deferred, and use
// font-display: block so the fallback font never has time to flash in
// before Caveat swaps in
(function () {
	if (document.getElementById("craft-hr-handwritten-font")) return;
	const link = document.createElement("link");
	link.id = "craft-hr-handwritten-font";
	link.rel = "stylesheet";
	link.href = "https://fonts.googleapis.com/css2?family=Caveat:wght@600&display=block";
	document.head.appendChild(link);
})();

function craft_hr_is_root_desktop_route() {
	const route = frappe.get_route();
	return route.length === 0 || (route.length === 1 && (route[0] === "desktop" || route[0] === ""));
}

craft_hr.render_desktop_greeting = function () {
	if (!craft_hr_is_root_desktop_route()) {
		$("#craft-hr-desktop-greeting").remove();
		return;
	}

	// only the top-level icons grid, never one rendered inside a bootstrap
	// modal (folder drill-down / "Removed Icons" pane reuse the same classes)
	const $container = $(".desktop-container").filter(function () {
		return $(this).closest(".modal").length === 0;
	});
	if (!$container.length) {
		$("#craft-hr-desktop-greeting").remove();
		return;
	}

	if ($(document).find("#craft-hr-desktop-greeting").length) return;

	// plain centered text, no card. Placed as a sibling BEFORE
	// .desktop-container entirely (not inside it) so it is never subject to
	// whatever flex/grid layout the icon grid itself uses.
	const $widget = $(
		`<div id="craft-hr-desktop-greeting" class="d-none d-md-block" style="
			text-align: center;
			margin: 16px 0 20px 0;
			width: 100%;
			box-sizing: border-box;
		">
			<span id="craft-hr-desktop-greeting-title" style="display: block; font-family: 'Caveat', cursive; font-size: 30px; font-weight: 600; color: #111827; line-height: 1.2;"></span>
			<span id="craft-hr-desktop-greeting-subtitle" style="display: block; font-size: 13px; font-weight: 500; color: #6b7280; margin-top: 2px;"></span>
		</div>`
	);

	$widget.insertBefore($container);

	function update() {
		if (!craft_hr_is_root_desktop_route()) return;
		const now = moment();
		const hour = now.hour();
		const greeting =
			hour < 12 ? __("Good morning") : hour < 17 ? __("Good afternoon") : __("Good evening");
		const fullname =
			(frappe.boot.user_info &&
				frappe.boot.user_info[frappe.session.user] &&
				frappe.boot.user_info[frappe.session.user].fullname) ||
			frappe.session.user;

		$widget.find("#craft-hr-desktop-greeting-title").text(`${greeting}, ${fullname}`);
		$widget.find("#craft-hr-desktop-greeting-subtitle").text(now.format("ddd, D MMMM YYYY, h:mm A"));
	}

	update();
	setInterval(update, 30 * 1000);
};

function craft_hr_sync_greeting_visibility() {
	// a folder drill-down opens as a Bootstrap modal overlay, which doesn't
	// trigger a route change — hide the greeting while any modal is open
	const $widget = $("#craft-hr-desktop-greeting");
	if (!$widget.length) return;
	const modalOpen = $(".modal.show, .modal.in").length > 0;
	$widget.toggle(!modalOpen);
}

function craft_hr_poll_until_rendered(attemptsLeft) {
	craft_hr.render_desktop_greeting();
	if ($("#craft-hr-desktop-greeting").length || attemptsLeft <= 0) return;
	setTimeout(() => craft_hr_poll_until_rendered(attemptsLeft - 1), 50);
}

function craft_hr_watch_desktop_page() {
	// try immediately, then keep polling quickly for a couple seconds in case
	// the icon grid hasn't rendered yet, so the greeting appears together
	// with the icons instead of visibly popping in afterwards
	craft_hr_poll_until_rendered(40);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", () => craft_hr_poll_until_rendered(40));
	}
	setInterval(craft_hr_sync_greeting_visibility, 500);
}

$(document).ready(craft_hr_watch_desktop_page);
