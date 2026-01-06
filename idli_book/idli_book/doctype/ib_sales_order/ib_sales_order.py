import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class IBSalesOrder(Document):
	pass

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	"""Convert Sales Order to Sales Invoice"""
	
	def set_missing_values(source, target):
		target.invoice_date = frappe.utils.today()
		target.sales_order_ref = source.name
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")
	
	def update_item(source, target, source_parent):
		# Items are mapped automatically
		pass
	
	doclist = get_mapped_doc(
		"IB Sales Order",
		source_name,
		{
			"IB Sales Order": {
				"doctype": "IB Sales Invoice",
				"field_map": {
					"name": "sales_order_ref",
				},
				"field_no_map": ["status"]
			},
			"IB Invoice Item": {
				"doctype": "IB Invoice Item",
				"field_no_map": []  # Copy all fields
			}
		},
		target_doc,
		set_missing_values
	)
	
	# Update Sales Order status to Invoiced (using db_set to bypass submit validation)
	sales_order = frappe.get_doc("IB Sales Order", source_name)
	sales_order.db_set("status", "Invoiced", update_modified=False)
	
	return doclist
