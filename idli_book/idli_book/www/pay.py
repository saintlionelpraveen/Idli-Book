import frappe
from frappe import _

def get_context(context):
	"""Context for payment page"""
	try:
		invoice_name = frappe.form_dict.get("invoice")
		
		if not invoice_name:
			context.error_message = "Invoice parameter is missing"
			return context
			
		# Verify invoice exists
		if not frappe.db.exists("IB Sales Invoice", invoice_name):
			context.error_message = f"Invoice {invoice_name} not found"
			return context
		
		# Get invoice details
		invoice = frappe.get_doc("IB Sales Invoice", invoice_name)
		
		# Check if payment is still needed
		if invoice.outstanding_amount <= 0:
			context.error_message = f"Invoice {invoice_name} is already paid"
			return context
		
		# Get payment settings
		settings = frappe.get_single("IB Payment Settings")
		org = frappe.get_single("IB Organization")
		
		# Populate context
		context.invoice_name = invoice.name
		context.customer = invoice.customer
		context.amount = invoice.outstanding_amount
		context.amount_paise = int(invoice.outstanding_amount * 100)
		context.currency = "INR"
		context.key_id = getattr(settings, 'razorpay_key_id', '')
		context.company = getattr(org, 'organization_name', 'Idli Book')
		
		return context
		
	except Exception as e:
		frappe.log_error("Payment Page Error", str(e))
		context.error_message = "An error occurred while loading the payment page"
		return context

