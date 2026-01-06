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
					if not self.paid_to_account:
						bank_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Bank"})
						if bank_account:
							self.paid_to_account = bank_account
						else:
							frappe.throw("Please select 'Paid To' account or create a Bank account in Chart of Accounts")
			
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
		bank_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Bank"})
		if bank_account:
			return bank_account
		
		# Create new
		org = frappe.get_doc("IB Organization", "IB Organization")
		org_name = org.organization_name if hasattr(org, 'organization_name') else "Organization"
		
		account = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": f"{org_name} - Bank",
			"account_type": "Bank",
			"root_type": "Asset",
			"is_group": 0
		})
		account.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return account.name
	
	def get_or_create_cash_account(self):
		"""Get existing Cash account or create one if it doesn't exist"""
		# Try to find existing Cash account
		cash_account = frappe.db.get_value("IB Chart of Accounts", {"account_type": "Cash"})
		if cash_account:
			return cash_account
		
		# Search by name
		cash_account = frappe.db.get_value("IB Chart of Accounts", {"account_name": ["like", "%Cash%"]})
		if cash_account:
			return cash_account
		
		# Get organization name for account naming
		org = frappe.get_doc("IB Organization", "IB Organization")
		org_name = org.organization_name if hasattr(org, 'organization_name') else "Organization"
		
		# Create new Cash account with clear naming
		account_name = f"{org_name} - Cash"
		cash_doc = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": account_name,
			"account_type": "Cash",
			"root_type": "Asset",
			"is_group": 0
		})
		cash_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
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
				
				# Validation
				if not cancel and (current_outstanding - alloc < -0.1): # Float tolerance
					frappe.throw(f"Cannot allocate {alloc} to {row.reference_name}. Outstanding is only {current_outstanding}")
				
				new_paid = current_paid + alloc
				new_outstanding = current_outstanding - alloc
				
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
