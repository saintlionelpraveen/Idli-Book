frappe.pages['ib-dash'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'IB Dash',
		single_column: true
	});
}