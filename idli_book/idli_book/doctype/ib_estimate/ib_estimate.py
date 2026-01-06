import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class IBEstimate(Document):
	pass

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	"""Convert Estimate to Sales Order"""
	
	def set_missing_values(source, target):
		target.order_date = frappe.utils.today()
		target.estimate_ref = source.name
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")
	
	def update_item(source, target, source_parent):
		# Items are mapped automatically; we just need to ensure all fields transfer
		pass
	
	doclist = get_mapped_doc(
		"IB Estimate",
		source_name,
		{
			"IB Estimate": {
				"doctype": "IB Sales Order",
				"field_map": {
					"name": "estimate_ref",
				}
			},
			"IB Invoice Item": {
				"doctype": "IB Invoice Item",
				"field_no_map": []  # Copy all fields
			}
		},
		target_doc,
		set_missing_values
	)
	
	# Update Estimate status to Accepted (using db_set to bypass submit validation)
	estimate = frappe.get_doc("IB Estimate", source_name)
	estimate.db_set("status", "Accepted", update_modified=False)
	
	return doclist
