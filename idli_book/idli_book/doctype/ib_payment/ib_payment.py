import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

@frappe.whitelist()
def fix_db_schema():
	# Robust schema fix triggered from client side
	try:
		# Attempt 1: Standard Modify
		frappe.db.sql("ALTER TABLE `tabIB Payment` MODIFY COLUMN `name` VARCHAR(140) NOT NULL")
		frappe.db.commit()
	except Exception:
		try:
			# Attempt 2: Drop Auto Increment
			frappe.db.sql("ALTER TABLE `tabIB Payment` MODIFY COLUMN `name` INT(11) NOT NULL") 
			frappe.db.sql("ALTER TABLE `tabIB Payment` DROP PRIMARY KEY")
			frappe.db.sql("ALTER TABLE `tabIB Payment` MODIFY COLUMN `name` VARCHAR(140) NOT NULL PRIMARY KEY")
			frappe.db.commit()
		except Exception:
			pass
			
	# Attempt 3: Fix Data (Migrate to Awaiting Payment)
	try:
		frappe.db.sql("UPDATE `tabIB Sales Invoice` SET status='Awaiting Payment' WHERE status IN ('Submitted', 'Pending')")
		frappe.db.commit()
	except Exception:
		pass

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
				# FROM: Customer Account (where money comes from)
				# TO: Our Cash/Bank Account (where money goes)
				
				# Get customer's receivable account
				customer_account = frappe.db.get_value("IB Customer", self.party, "default_receivable_account")
				if not customer_account:
					customer_account = org.default_receivable_account
				
				self.paid_from_account = customer_account
				
				# Get our cash/bank account based on mode
				if self.mode_of_payment == "Cash":
					self.paid_to_account = self.get_or_create_cash_account()
				else:
					# For Bank Transfer/Cheque
					# For Bank Transfer/Cheque
					if not self.paid_to_account:
						bank_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Bank"})
						if not bank_account:
							bank_account = self.get_or_create_bank_account()
						self.paid_to_account = bank_account
			
			elif self.payment_type == "Pay":
				# PAY: We pay vendor
				# FROM: Our Cash/Bank Account (where money comes from)
				# TO: Vendor Account (where money goes)
				
				# Get vendor's payable account
				vendor_account = frappe.db.get_value("IB Vendor", self.party, "default_payable_account")
				if not vendor_account:
					# Try organization default
					vendor_account = org.default_payable_account if hasattr(org, 'default_payable_account') else None
				
				if not vendor_account:
					# Auto-create vendor account
					vendor_account = self.create_vendor_account()
				
				self.paid_to_account = vendor_account
				
				# Get our cash/bank account based on mode
				if self.mode_of_payment == "Cash":
					self.paid_from_account = self.get_or_create_cash_account()
				else:
					if not self.paid_from_account:
						bank_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Bank"})
						if not bank_account:
							# Auto-create bank account
							bank_account = self.get_or_create_bank_account()
						self.paid_from_account = bank_account

		self.calculate_unallocated()
		
		# Clear references if amended to prevent linking to cancelled documents
		if self.amended_from and self.docstatus == 0:
			self.clear_amended_payment_references()

	def clear_amended_payment_references(self):
		"""Remove references from the cancelled payment"""
		try:
			# Clear allocation references from old payment
			frappe.db.sql("""
				DELETE FROM `tabIB Payment Reference`
				WHERE parent = %s
			""", self.amended_from)
			frappe.msgprint(f"Cleared references from cancelled payment {self.amended_from}")
		except Exception as e:
			frappe.log_error("Amendment Cleanup Failed", str(e))
	
	def create_vendor_account(self):
		"""Create payable account for vendor"""
		vendor_name = frappe.db.get_value("IB Vendor", self.party, "vendor_name")
		account_name = f"Vendor - {vendor_name}"
		
		# Check if exists
		existing = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_name})
		if existing:
			return existing
		
		# Create new
		account = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": account_name,
			"account_type": "Payable",
			"root_type": "Liability",
			"is_group": 0
		})
		account.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Update vendor
		frappe.db.set_value("IB Vendor", self.party, "default_payable_account", account.name)
		
		return account.name

	def get_or_create_bank_account(self):
		"""Get or create default bank account"""
		# Try to find existing
		bank_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Bank"}, "name")
		if bank_account:
			return bank_account
		
		# Create new
		org = frappe.get_doc("IB Organization", "IB Organization")
		org_name = org.organization_name if hasattr(org, 'organization_name') else "Organization"
		ac_name = f"{org_name} - Bank"
		
		# Check by name to avoid duplicate error
		existing_by_name = frappe.db.get_value("IB Chart of Accounts", {"account_name": ac_name}, "name")
		if existing_by_name: 
			return existing_by_name

		account = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": ac_name,
			"account_type": "Bank",
			"root_type": "Asset",
			"is_group": 0
		})
		account.insert(ignore_permissions=True)
		
		return account.name
	
	def get_or_create_cash_account(self):
		"""Get existing Cash account or create one if it doesn't exist"""
		# Try to find existing Cash account
		cash_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Cash"}, "name")
		if cash_account:
			return cash_account
		
		# Get organization name for account naming
		org = frappe.get_doc("IB Organization", "IB Organization")
		org_name = org.organization_name if hasattr(org, 'organization_name') else "Organization"
		
		# Create new Cash account with clear naming
		account_name = f"{org_name} - Cash"
		
		# Check by name first
		existing_by_name = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_name}, "name")
		if existing_by_name:
			return existing_by_name
			
		cash_doc = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": account_name,
			"account_type": "Cash",
			"root_type": "Asset",
			"is_group": 0
		})
		cash_doc.insert(ignore_permissions=True)
		
		return cash_doc.name
	
	def set_dates(self):
		if not self.payment_date:
			self.payment_date = nowdate()

	def calculate_unallocated(self):
		total_allocated = 0
		for row in self.references:
			total_allocated += flt(row.allocated_amount)
		
		# Auto-correct allocation if user forgot to update table (Single Row only)
		if total_allocated > self.amount + 0.1:
			if len(self.references) == 1:
				self.references[0].allocated_amount = self.amount
				total_allocated = self.amount
				# frappe.msgprint("Auto-adjusted allocated amount to match Payment Amount.")
			else:
				frappe.throw("Total allocated amount cannot exceed Payment Amount")
			
		self.unallocated_amount = self.amount - total_allocated

	def on_submit(self):
		# Set posting_date for GL Engine
		self.posting_date = self.payment_date
		self.make_gl_entries()
		self.update_references(cancel=False)
		self.send_payment_email()

	def send_payment_email(self):
		if not self.party: return

		# 1. Customer Payment Receipt
		if self.party_type == "IB Customer":
			customer_email = frappe.db.get_value("IB Customer", self.party, "email")
			if not customer_email: return

			org_name = frappe.db.get_single_value('IB Organization', 'organization_name') or "Our Company"
			subject = f"Payment Received - Thank You | {org_name}"
			
			# ... (Existing Customer Logic) ...
			# I will rewrite the whole method to keep it clean and include Vendor logic
			
			self.send_customer_email(customer_email, org_name, subject)

		# 2. Vendor Payment Advice
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
				<p>Please find the details attached.</p>
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
		# Gather details from linked invoices
		details_html = ""
		attachments = []
		
		for ref in self.references:
			if ref.reference_doctype == "IB Sales Invoice" and ref.reference_name:
				inv = frappe.get_doc("IB Sales Invoice", ref.reference_name)
				
				# Status Badge
				status_color = "#28a745" if inv.outstanding_amount <= 0.1 else "#ffc107"
				status_text = "Fully Paid" if inv.outstanding_amount <= 0.1 else "Partially Paid"
				
				# Due Date Display
				due_date_html = ""
				if inv.outstanding_amount > 0.1:
					due_date_html = f"""
					<div style="margin-top:5px;">
						<span style="color: #666;">Due Date: </span> 
						<strong style="color: #dc3545;">{frappe.utils.formatdate(inv.due_date)}</strong>
					</div>
					"""

				details_html += f"""
				<div style="border: 1px solid #eee; padding: 15px; margin-bottom: 10px; border-radius: 8px;">
					<h4 style="margin: 0 0 10px 0; color: #333;">Invoice #{inv.name}</h4>
					<table width="100%" style="font-size: 14px;">
						<tr>
							<td style="color: #666;">Invoiced Amount:</td>
							<td><strong>{frappe.format(inv.grand_total, {'fieldtype': 'Currency'})}</strong></td>
						</tr>
						<tr>
							<td style="color: #666;">Payment Applied:</td>
							<td style="color: #28a745;"><strong>- {frappe.format(ref.allocated_amount, {'fieldtype': 'Currency'})}</strong></td>
						</tr>
					</table>
					<div style="margin-top: 10px;">
						<span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
							{status_text}
						</span>
						{due_date_html}
					</div>
				</div>
				"""
				try:
					attachments.append(frappe.attach_print(ref.reference_doctype, ref.reference_name, print_format="Standard"))
				except: pass

		message = f"""
		<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
			<h2 style="color: #2c3e50;">Payment Confirmation</h2>
			<p>Hello {self.party},</p>
			
			<p>We have successfully received your payment of <b style="font-size: 18px; color: #28a745;">{frappe.format(self.amount, {'fieldtype': 'Currency'})}</b>.</p>
			
			<p>Thank you for your business! Below are the details of the updated invoice status:</p>
			
			{details_html}
			
			<br>
			<p>We truly appreciate your prompt payment.</p>
			<br>
			<p style="color: #777; font-size: 13px;">Warm Regards,<br><b>{org_name}</b></p>
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
		
		# 1. Bank/Cash Side (Paid To for Receive, Paid From for Pay)
		# 2. Party Side (Paid From for Receive, Paid To for Pay)

		# Receive: Dr Bank, Cr Customer
		# Pay: Dr Vendor, Cr Bank
		
		# In our form:
		# Receive: Paid To = Bank, Paid From = Customer Acct
		# Pay: Paid From = Bank, Paid To = Vendor Acct
		
		# So universal logic based on form fields:
		# Dr Paid To Account
		# Cr Paid From Account
		
		# Add Party info for reconciliation
		party_type = self.party_type if self.party else None
		party = self.party if self.party else None
		
		# Entry 1: Debit Paid To
		gl_entries.append({
			"account": self.paid_to_account,
			"debit": self.amount,
			"credit": 0,
			"remarks": f"{self.payment_type} - {self.party}",
			# If Pay, Paid To is Vendor. Map Party.
			"party_type": party_type if self.payment_type == "Pay" else None,
			"party": party if self.payment_type == "Pay" else None
		})
		
		# Entry 2: Credit Paid From
		gl_entries.append({
			"account": self.paid_from_account,
			"debit": 0,
			"credit": self.amount,
			"remarks": f"{self.payment_type} - {self.party}",
			# If Receive, Paid From is Customer. Map Party.
			"party_type": party_type if self.payment_type == "Receive" else None,
			"party": party if self.payment_type == "Receive" else None
		})
		
		GLEngine.make_gl_entries(self, gl_entries)

	def update_references(self, cancel=False):
		# Update Paid Amount in Invoices/Bills
		for row in self.references:
			factor = -1 if cancel else 1
			if row.reference_doctype and row.reference_name:
				doc = frappe.get_doc(row.reference_doctype, row.reference_name)
				current_paid = flt(doc.paid_amount)
				current_outstanding = flt(doc.outstanding_amount)
				
				alloc = flt(row.allocated_amount) * factor
				
				# Validation: Prevent Overpayment
				# Tolerance 0.1 allows rounding diffs, but prevents user paying 2000 for 1000 bill
				if not cancel and (current_outstanding - alloc < -1.0): 
					frappe.throw(f"Excess Payment! Allocated {alloc} but only {current_outstanding} is pending for {row.reference_name}.")
				
				new_paid = current_paid + alloc
				new_outstanding = current_outstanding - alloc
				
				# Floor negative small values to 0
				if new_outstanding < 0: new_outstanding = 0
				
				frappe.db.set_value(row.reference_doctype, row.reference_name, "paid_amount", new_paid)
				frappe.db.set_value(row.reference_doctype, row.reference_name, "outstanding_amount", new_outstanding)
				
				status = "Awaiting Payment"
				if new_outstanding <= 0.1: # Float tolerance
					status = "Paid"
				elif new_paid > 0:
					status = "Partially Paid"
				else:
					status = "Awaiting Payment" if doc.docstatus==1 else "Draft"
				
				# Update status and log for debugging
				frappe.db.set_value(row.reference_doctype, row.reference_name, "status", status)
				frappe.msgprint(f"Updated {row.reference_name}: Status={status}, Paid={new_paid}, Outstanding={new_outstanding}")
