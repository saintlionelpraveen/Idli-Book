import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class IBPurchaseOrder(Document):
	def validate(self):
		self.calculate_totals()
	
	def calculate_totals(self):
		"""Calculate totals similar to Sales Invoice"""
		subtotal = 0.0
		total_tax = 0.0
		
		for row in self.items:
			if not row.quantity:
				row.quantity = 0
			if not row.rate:
				row.rate = 0
			
			# Calculate line amount
			row.amount = flt(row.quantity) * flt(row.rate)
			
			# Calculate tax if applicable
			row_tax = 0.0
			if row.tax_rate:
				row_tax = row.amount * (row.tax_rate / 100)
			
			subtotal += row.amount
			total_tax += row_tax
		
		self.subtotal = flt(subtotal)
		self.tax_amount = flt(total_tax)
		
		# Apply discount
		discount = flt(self.discount_amount) if self.discount_amount else 0
		
		# Calculate grand total
		self.grand_total = flt(self.subtotal + self.tax_amount - discount)
	
	def on_submit(self):
		self.status = "Issued"

@frappe.whitelist()
def make_purchase_bill(source_name):
	"""Create Purchase Bill from Purchase Order"""
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		target.purchase_order = source.name
		target.run_method("calculate_totals")
	
	doclist = get_mapped_doc("IB Purchase Order", source_name, {
		"IB Purchase Order": {
			"doctype": "IB Purchase Bill",
			"field_map": {
				"vendor": "vendor",
				"order_date": "bill_date"
			}
		},
		"IB Invoice Item": {
			"doctype": "IB Purchase Item",
			"field_map": {
				"item_code": "item",
				"item_name": "item_name",
				"description": "description",
				"quantity": "qty",
				"uom": "uom",
				"rate": "rate",
				"amount": "amount",
				"tax_rate": "tax_percentage"
			}
		}
	}, target_doc=None, postprocess=set_missing_values)
	
	return doclist
