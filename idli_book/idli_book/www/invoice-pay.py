import frappe
from frappe import _

no_cache = 1

def get_context(context):
	"""Generate UPI payment page with QR code"""
	invoice_name = frappe.form_dict.get("invoice")
	
	if not invoice_name:
		context.error_message = "Invoice parameter is missing"
		return context
	
	# Get invoice
	try:
		invoice = frappe.get_doc("IB Sales Invoice", invoice_name)
	except:
		context.error_message = f"Invoice {invoice_name} not found"
		return context
	
	# Check if already paid
	if invoice.outstanding_amount <= 0:
		context.paid = True
		context.invoice_name = invoice.name
		context.customer = invoice.customer
		return context
	
	# Get settings
	settings = frappe.get_single("IB Payment Settings")
	org = frappe.get_single("IB Organization")
	
	upi_enabled = getattr(settings, 'enable_upi_qr', 0)
	upi_id = getattr(settings, 'upi_id', None)
	
	# Check UPI enabled
	if not upi_enabled or not upi_id:
		context.error_message = "UPI payment is not configured. Please contact the administrator."
		return context
	
	# Generate UPI QR Code
	try:
		import qrcode
		from io import BytesIO
		import base64
		
		# Build UPI URI
		payee_name = getattr(settings, 'payee_name', None) or getattr(org, 'organization_name', 'Merchant')
		amount = invoice.outstanding_amount
		
		upi_uri = f"upi://pay?pa={upi_id}&pn={payee_name}&tr={invoice.name}&tn=Invoice {invoice.name}&am={amount}&cu=INR"
		
		# Generate QR
		qr = qrcode.QRCode(version=1, box_size=10, border=4)
		qr.add_data(upi_uri)
		qr.make(fit=True)
		
		img = qr.make_image(fill_color="black", back_color="white")
		buffered = BytesIO()
		img.save(buffered, format="PNG")
		qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
		
		# Populate context
		context.invoice_name = invoice.name
		context.customer = invoice.customer
		context.invoice_date = frappe.utils.formatdate(invoice.invoice_date)
		context.due_date = frappe.utils.formatdate(invoice.due_date)
		context.amount = invoice.outstanding_amount
		context.grand_total = invoice.grand_total
		context.paid_amount = invoice.paid_amount or 0
		context.status = invoice.status
		context.qr_code = qr_code_base64
		context.upi_id = upi_id
		context.payee_name = payee_name
		context.company = getattr(org, 'organization_name', 'Idli Book')
		
	except ImportError:
		context.error_message = "QR code library not installed. Please run: ./env/bin/pip install qrcode[pil]"
		return context
	except Exception as e:
		frappe.log_error("Payment Page Error", str(e))
		context.error_message = f"Error: {str(e)}"
		return context
	
	return context

