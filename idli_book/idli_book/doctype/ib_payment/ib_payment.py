import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class IBPayment(Document):
	@property
	def status(self):
		if self.docstatus == 0: return "Draft"
		if self.docstatus == 1: return "Submitted"
		if self.docstatus == 2: return "Cancelled"
			
	def validate(self):
		self.set_dates()
		
		# Auto-fill accounts based on payment type and party
		if self.party_type and self.party:
			org = frappe.get_doc("IB Organization", "IB Organization")
			
			if self.payment_type == "Receive":
				# RECEIVE: Customer pays us
				# Get customer's linked receivable account or org default
				customer_account = frappe.db.get_value("IB Customer", self.party, "default_receivable_account")
				if not customer_account:
					customer_account = org.default_receivable_account
				
				self.paid_from_account = customer_account
				
				# Get our cash/bank account based on mode
				if self.mode_of_payment == "Cash":
					self.paid_to_account = org.default_cash_account
				else:
					if not self.paid_to_account:
						self.paid_to_account = org.default_bank_account
			
			elif self.payment_type == "Pay":
				# PAY: We pay vendor
				# Get vendor's linked payable account or org default
				vendor_account = frappe.db.get_value("IB Vendor", self.party, "default_payable_account")
				if not vendor_account:
					vendor_account = org.default_payable_account
				
				self.paid_to_account = vendor_account
				
				# Get our cash/bank account based on mode
				if self.mode_of_payment == "Cash":
					self.paid_from_account = org.default_cash_account
				else:
					if not self.paid_from_account:
						self.paid_from_account = org.default_bank_account

		self.calculate_unallocated()
		
		if self.amended_from and self.docstatus == 0:
			self.clear_amended_payment_references()

	def clear_amended_payment_references(self):
		try:
			frappe.db.sql("""
				DELETE FROM `tabIB Payment Reference`
				WHERE parent = %s
			""", self.amended_from)
			frappe.msgprint(f"Cleared references from cancelled payment {self.amended_from}")
		except Exception as e:
			frappe.log_error("Amendment Cleanup Failed", str(e))
	
	def set_dates(self):
		if not self.payment_date:
			self.payment_date = nowdate()

	def calculate_unallocated(self):
		total_allocated = 0
		for row in self.references:
			total_allocated += flt(row.allocated_amount)
		
		if total_allocated > self.amount + 0.1:
			if len(self.references) == 1:
				self.references[0].allocated_amount = self.amount
				total_allocated = self.amount
			else:
				frappe.throw("Total allocated amount cannot exceed Payment Amount")
			
		self.unallocated_amount = self.amount - total_allocated

	def on_submit(self):
		self.posting_date = self.payment_date
		self.make_gl_entries()
		self.update_references(cancel=False)
		self.send_payment_email()

	def send_payment_email(self):
		if not self.party: return

		if self.party_type == "IB Customer":
			customer_email = frappe.db.get_value("IB Customer", self.party, "email")
			if not customer_email: return

			org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
			subject = f"Payment Received - Thank You | {org_name}"
			
			self.send_customer_email(customer_email, org_name, subject)

		elif self.party_type == "IB Vendor":
			vendor_email = frappe.db.get_value("IB Vendor", self.party, "email")
			if not vendor_email: return
			
			org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
			subject = f"Payment Advice - {self.name} | {org_name}"
			
			message = f"""
			<div style="font-family: Arial, sans-serif; padding: 20px;">
				<h3>Payment Advice</h3>
				<p>Hello {self.party},</p>
				<p>We have processed a payment of <b style="color: #d63384;">{frappe.format(self.amount, {'fieldtype': 'Currency'})}</b> to you.</p>
				<p><b>Reference:</b> {self.reference_no or 'N/A'}</p>
				<p><b>Payment Date:</b> {frappe.utils.formatdate(self.payment_date)}</p>
				<br>
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
				frappe.msgprint(f"Payment Advice sent to {vendor_email} (CC: You)")
				self.db_set('email_delivery_status', 'Sent')
			except Exception as e:
				frappe.log_error("Payment Email Failed", str(e))
				self.db_set('email_delivery_status', 'Error')

	def send_customer_email(self, email, org_name, subject):
		details_html = ""
		attachments = []
		
		for ref in self.references:
			if ref.reference_doctype == "IB Sales Invoice" and ref.reference_name:
				inv = frappe.get_doc("IB Sales Invoice", ref.reference_name)
				
				status_color = "#28a745" if inv.outstanding_amount <= 0.1 else "#ffc107"
				status_text = "Fully Paid" if inv.outstanding_amount <= 0.1 else "Partially Paid"

				details_html += f"""
				<div style="border: 1px solid #eee; padding: 15px; margin-bottom: 10px; border-radius: 8px;">
					<h4 style="margin: 0 0 10px 0; color: #333;">Invoice #{inv.name}</h4>
					<p>Amount: <strong>{frappe.format(inv.grand_total, {'fieldtype': 'Currency'})}</strong></p>
					<p>Payment Applied: <strong style="color: #28a745;">- {frappe.format(ref.allocated_amount, {'fieldtype': 'Currency'})}</strong></p>
					<span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{status_text}</span>
				</div>
				"""
				try:
					attachments.append(frappe.attach_print(ref.reference_doctype, ref.reference_name, print_format="Standard"))
				except: pass

		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
			<h2 style="color: #2c3e50;">Payment Confirmation</h2>
			<p>Hello {self.party},</p>
			<p>We have received your payment of <b style="font-size: 18px; color: #28a745;">{frappe.format(self.amount, {'fieldtype': 'Currency'})}</b>.</p>
			{details_html}
			<br>
			<p>Thank you for your business!</p>
			<p style="color: #777;">Best Regards,<br><b>{org_name}</b></p>
		</div>
		"""
		
		try:
			frappe.sendmail(
				recipients=email,
				subject=subject,
				message=message,
				attachments=attachments,
				reference_doctype=self.doctype,
				reference_name=self.name
			)
			frappe.msgprint(f"Payment acknowledgement sent to {email}")
			self.db_set('email_delivery_status', 'Sent')
		except Exception as e:
			frappe.log_error("Payment Email Failed", str(e))
			self.db_set('email_delivery_status', 'Error')

	def on_cancel(self):
		from idli_book.idli_book.gl_engine import GLEngine
		GLEngine.delete_gl_entries(self)
		self.update_references(cancel=True)

	def make_gl_entries(self):
		from idli_book.idli_book.gl_engine import GLEngine
		
		gl_entries = []
		
		party_type = self.party_type if self.party else None
		party = self.party if self.party else None
		
		# Entry 1: Debit Paid To
		gl_entries.append({
			"account": self.paid_to_account,
			"debit": self.amount,
			"credit": 0,
			"remarks": f"{self.payment_type} - {self.party}",
			"party_type": party_type if self.payment_type == "Pay" else None,
			"party": party if self.payment_type == "Pay" else None
		})
		
		# Entry 2: Credit Paid From
		gl_entries.append({
			"account": self.paid_from_account,
			"debit": 0,
			"credit": self.amount,
			"remarks": f"{self.payment_type} - {self.party}",
			"party_type": party_type if self.payment_type == "Receive" else None,
			"party": party if self.payment_type == "Receive" else None
		})
		
		GLEngine.make_gl_entries(self, gl_entries)

	def update_references(self, cancel=False):
		for row in self.references:
			factor = -1 if cancel else 1
			if row.reference_doctype and row.reference_name:
				doc = frappe.get_doc(row.reference_doctype, row.reference_name)
				current_paid = flt(doc.paid_amount)
				current_outstanding = flt(doc.outstanding_amount)
				
				alloc = flt(row.allocated_amount) * factor
				
				if not cancel and (current_outstanding - alloc < -1.0): 
					frappe.throw(f"Excess Payment! Allocated {alloc} but only {current_outstanding} is pending for {row.reference_name}.")
				
				new_paid = current_paid + alloc
				new_outstanding = current_outstanding - alloc
				
				if new_outstanding < 0: new_outstanding = 0
				
				frappe.db.set_value(row.reference_doctype, row.reference_name, "paid_amount", new_paid)
				frappe.db.set_value(row.reference_doctype, row.reference_name, "outstanding_amount", new_outstanding)
				
				status = "Awaiting Payment"
				if new_outstanding <= 0.1:
					status = "Paid"
				elif new_paid > 0:
					status = "Partially Paid"
				else:
					status = "Awaiting Payment" if doc.docstatus==1 else "Draft"
				
				frappe.db.set_value(row.reference_doctype, row.reference_name, "status", status)
				frappe.msgprint(f"Updated {row.reference_name}: Status={status}, Paid={new_paid}, Outstanding={new_outstanding}")
