import frappe
from frappe import _
from frappe.utils import flt, get_url
import razorpay
import hmac
import hashlib

def get_razorpay_client():
	settings = frappe.get_single("IB Payment Settings")
	if not settings.enable_payment_gateway:
		frappe.throw(_("Payment Gateway is disabled"))
	
	if not settings.razorpay_key_id or not settings.razorpay_key_secret:
		frappe.throw(_("Razorpay Keys are not configured"))
		
	return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret_password))

@frappe.whitelist(allow_guest=True)
def get_payment_details(invoice_name):
	"""Returns details needed for the payment page"""
	try:
		doc = frappe.get_doc("IB Sales Invoice", invoice_name)
		settings = frappe.get_single("IB Payment Settings")
		
		return {
			"invoice_name": doc.name,
			"customer": doc.customer,
			"amount": doc.outstanding_amount,
			"currency": "INR", # Assuming INR for now
			"key_id": settings.razorpay_key_id,
			"company": frappe.db.get_single_value('IB Organization', 'organization_name') or "Idli Book"
		}
	except Exception as e:
		frappe.log_error("Payment Details Error", str(e))
		return {"error": str(e)}

@frappe.whitelist(allow_guest=True)
def create_razorpay_order(invoice_name):
	"""Create Order ID in Razorpay"""
	try:
		doc = frappe.get_doc("IB Sales Invoice", invoice_name)
		client = get_razorpay_client()
		
		amount_in_paise = int(flt(doc.outstanding_amount) * 100)
		
		order_data = {
			"amount": amount_in_paise,
			"currency": "INR",
			"receipt": invoice_name,
			"notes": {
				"invoice_id": invoice_name,
				"customer": doc.customer
			}
		}
		
		order = client.order.create(data=order_data)
		return {"order_id": order['id']}
		
	except Exception as e:
		frappe.log_error("Razorpay Order Error", str(e))
		frappe.throw(_("Could not initiate payment: ") + str(e))

@frappe.whitelist(allow_guest=True)
def verify_payment(razorpay_payment_id, razorpay_order_id, razorpay_signature, invoice_name):
	"""Verify signature and create Payment Entry"""
	try:
		settings = frappe.get_single("IB Payment Settings")
		client = get_razorpay_client()
		
		# Verify Signature
		params_dict = {
			'razorpay_order_id': razorpay_order_id,
			'razorpay_payment_id': razorpay_payment_id,
			'razorpay_signature': razorpay_signature
		}
		
		# Razorpay SDK verification
		client.utility.verify_payment_signature(params_dict)
		
		# If we reached here, payment is successful
		create_payment_entry(invoice_name, razorpay_payment_id)
		
		return {"status": "success", "message": "Payment Verified"}
		
	except razorpay.errors.SignatureVerificationError:
		frappe.log_error("Payment Verification Failed", f"Inv: {invoice_name}")
		frappe.throw(_("Payment Verification Failed"))
	except Exception as e:
		frappe.log_error("Payment Error", str(e))
		frappe.throw(str(e))

def create_payment_entry(invoice_name, payment_ref):
	# Create authorized session for system updates
	# Since this is guest access, we might need to ignore permissions or switch user context
	# For simplicity/safety, we'll use ignore_permissions=True on document methods
	
	try:
		inv = frappe.get_doc("IB Sales Invoice", invoice_name)
		
		# Avoid duplicate payments
		existing = frappe.db.exists("IB Payment", {"reference_no": payment_ref})
		if existing:
			return
		
		payment = frappe.new_doc("IB Payment")
		payment.payment_type = "Receive"
		payment.party_type = "IB Customer"
		payment.party = inv.customer
		payment.payment_date = frappe.utils.nowdate()
		payment.amount = inv.outstanding_amount
		payment.reference_no = payment_ref
		payment.reference_date = frappe.utils.nowdate()
		
		payment.append("references", {
			"reference_doctype": "IB Sales Invoice",
			"reference_name": inv.name,
			"total_amount": inv.grand_total,
			"outstanding_amount": inv.outstanding_amount,
			"allocated_amount": inv.outstanding_amount
		})
		
		payment.insert(ignore_permissions=True)
		payment.submit()
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error("Auto Payment Creation Failed", str(e))
		# Don't throw here to avoid rolling back the successful verfication message to user
		# But admins should check logs
