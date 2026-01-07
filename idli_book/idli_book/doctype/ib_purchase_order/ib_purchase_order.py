import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class IBPurchaseOrder(Document):
	def validate(self):
		if self.delivery_date and self.order_date:
			if self.delivery_date < self.order_date:
				frappe.throw("Expected Delivery Date cannot be before Order Date")
		self.calculate_totals()

	def on_submit(self):
		self.status = "Issued"
		self.send_po_email()
		
	def send_po_email(self):
		# Send PO to Vendor
		vendor_email = frappe.db.get_value("IB Vendor", self.vendor, "email")
		if vendor_email:
			org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
			subject = f"Purchase Order #{self.name} from {org_name}"
			
			message = f"""
			<div style="font-family: Arial, sans-serif; padding: 20px;">
				<h3>Purchase Order</h3>
				<p>Hello {self.vendor},</p>
				<p>Please find attached Purchase Order <b>#{self.name}</b> for your reference.</p>
				<p>We expect delivery by: <b>{frappe.utils.formatdate(self.delivery_date) if self.delivery_date else 'As soon as possible'}</b></p>
				<table style="width: 100%; border: 1px solid #ddd; margin-top: 20px;">
					<tr style="background: #f0f0f0;">
						<td style="padding:10px;">Total Amount</td>
						<td style="padding:10px; font-weight:bold;">{frappe.format(self.grand_total, {'fieldtype': 'Currency'})}</td>
					</tr>
				</table>
				<br>
				<p>Please confirm receipt and expected delivery date.</p>
				<p>Best Regards,<br>{org_name}</p>
			</div>
			"""
			
			try:
				frappe.sendmail(
					recipients=vendor_email,
					cc=[frappe.session.user], 
					subject=subject,
					message=message,
					reference_doctype=self.doctype,
					reference_name=self.name,
					attachments=[frappe.attach_print(self.doctype, self.name, print_format="Standard")]
				)
				self.db_set('email_delivery_status', 'Queued')
				frappe.msgprint(f"PO sent to {vendor_email} (CC: You)")
			except Exception:
				self.db_set('email_delivery_status', 'Error')

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
