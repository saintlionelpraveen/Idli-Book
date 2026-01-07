import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class IBSalesOrder(Document):
	def validate(self):
		# Date validation
		if self.shipment_date and self.order_date:
			if self.shipment_date < self.order_date:
				frappe.throw("Shipment Date cannot be before Order Date")
		
		# Stock availability validation
		self.validate_stock_availability()
	
	def validate_stock_availability(self):
		"""Check if enough stock is available for items"""
		for row in self.items:
			item_doc = frappe.get_doc("IB Item", row.item_code)
			
			# Only validate if item tracks inventory
			if item_doc.track_inventory:
				available_qty = item_doc.stock_quantity or 0
				requested_qty = row.quantity or 0
				
				if requested_qty > available_qty:
					frappe.throw(
						f"Insufficient stock for <b>{item_doc.item_name}</b>!<br>"
						f"Available: <b>{available_qty} {row.uom}</b><br>"
						f"Requested: <b>{requested_qty} {row.uom}</b><br><br>"
						f"Please reduce quantity or update stock.",
						title="Stock Not Available"
					)

	def on_submit(self):
		self.db_set("status", "To Deliver")
		self.send_order_email()

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def send_order_email(self):
		# Get Customer Email
		customer_email = frappe.db.get_value("IB Customer", self.customer, "email")
		if not customer_email:
			frappe.msgprint("Note: Customer has no email, Order email not sent.")
			return

		org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
		subject = f"Sales Order #{self.name} Confirmed - {org_name}"
		
		ship_date_display = frappe.utils.formatdate(self.shipment_date) if self.shipment_date else "TBD"
		
		# HTML Message with Highlighted Shipment Date
		message = f"""
		<div style="font-family: Arial, sans-serif; padding: 20px;">
			<h3>Order Confirmation</h3>
			<p>Hello {self.customer},</p>
			<p>Thank you for your order! We have received your Sales Order <b>#{self.name}</b>.</p>
			
			<div style="background-color: #e8f4fd; padding: 15px; border-left: 5px solid #007bff; margin: 20px 0;">
				<p style="margin: 0; color: #444;"><strong>Expected Shipment Date:</strong></p>
				<h2 style="margin: 5px 0 0 0; color: #007bff;">{ship_date_display}</h2>
			</div>

			<p>Total Amount: <b>{frappe.format(self.grand_total, {'fieldtype': 'Currency'})}</b></p>
			<p>You will receive another notification when the items are shipped.</p>
			<br>
			<p>Best Regards,<br>{org_name}</p>
		</div>
		"""
		
		# Send Email
		try:
			frappe.sendmail(
				recipients=customer_email,
				subject=subject,
				message=message,
				reference_doctype=self.doctype,
				reference_name=self.name,
				attachments=[frappe.attach_print(self.doctype, self.name, print_format="Standard")]
			)
			frappe.msgprint(f"Order confirmation sent to {customer_email}")
			self.db_set('email_delivery_status', 'Queued')
		except Exception as e:
			frappe.log_error("SO Email Failed", str(e))
			self.db_set('email_delivery_status', 'Error')
			frappe.msgprint("Failed to queue email.")

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
