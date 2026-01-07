import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class IBEstimate(Document):
	def on_submit(self):
		self.db_set("status", "Submitted")
		# Auto-Send Email
		self.send_approval_email()

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def send_approval_email(self):
		from frappe.utils import get_url
		
		# Get Customer Email
		customer_email = frappe.db.get_value("IB Customer", self.customer, "email")
		if not customer_email:
			frappe.msgprint("Note: Customer has no email, approval email not sent.")
			return

		# Generate Secure Links
		# Token security: Hash of Name + Creation time ensures it's unique and valid for this doc
		token = frappe.utils.data.generate_hash(self.name + str(self.creation), length=10)
		base_url = get_url()
		
		# API Endpoints
		accept_url = f"{base_url}/api/method/idli_book.idli_book.api.workflow.handle_estimate_response?name={self.name}&action=accept&token={token}"
		reject_url = f"{base_url}/api/method/idli_book.idli_book.api.workflow.handle_estimate_response?name={self.name}&action=reject&token={token}"
		
		# --- LOCAL DEV HELPER ---
		print("\n" + "="*50)
		print(f"📧 [DEV] EMAIL NOT SENT? USE THESE LINKS:")
		print(f"✅ ACCEPT: {accept_url}")
		print(f"❌ REJECT: {reject_url}")
		print("="*50 + "\n")
		# ------------------------
		
		org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
		subject = f"Estimate #{self.name} from {org_name}"
		
		# HTML Message - Simple Warm Welcome
		message = f"""
		<div style="font-family: Arial, sans-serif; padding: 20px;">
			<h3>Hello {self.customer},</h3>
			<p>Hope you are doing well!</p>
			<p>Please find attached your estimate <b>#{self.name}</b> for <b>{frappe.format(self.grand_total, {'fieldtype': 'Currency'})}</b>.</p>
			<p>We look forward to your feedback.</p>
			<br>
			<p>Warm Regards,<br>{org_name}</p>
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
			frappe.msgprint(f"Estimate sent to {customer_email}")
			self.db_set('email_delivery_status', 'Queued')
		except Exception as e:
			frappe.log_error("Email Failed", str(e))
			self.db_set('email_delivery_status', 'Error')
			frappe.msgprint("Failed to queue email. Check Error Log.")

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc
	
	def set_missing_values(source, target):
		target.estimate_ref = source.name
		target.order_date = frappe.utils.today()
		
		# Copy Items
		# Assuming target has 'items' table mapped
		pass

	doclist = get_mapped_doc("IB Estimate", source_name, {
		"IB Estimate": {
			"doctype": "IB Sales Order",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"IB Invoice Item": {
			"doctype": "IB Invoice Item",
			"field_map": {
				"parent": "estimate_ref"
			}
		}
	}, target_doc, set_missing_values)

	return doclist
