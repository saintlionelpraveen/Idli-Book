# Copyright (c) 2025, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IBCustomer(Document):
	"""
	IB Customer Doctype Controller
	
	Auto-creates receivable account in IB Chart of Accounts with naming:
	'Customer - {Customer Name} - Receivable'
	"""
	
	def before_save(self):
		"""Create linked account if not already set"""
		if not self.default_receivable_account:
			self.default_receivable_account = self.create_receivable_account()
		else:
			# Update bank details on existing account
			self.update_account_bank_details()
	
	def create_receivable_account(self):
		"""Create a receivable account for this customer"""
		account_name = f"Customer - {self.customer_name} - Receivable"
		
		# Check if account already exists
		if frappe.db.exists("IB Chart of Accounts", account_name):
			return account_name
		
		# Bank details from customer
		bank_details = {
			"bank_name": self.bank_name,
			"bank_account_number": self.bank_account_number,
			"ifsc_code": self.ifsc_code
		}
		
		# Create new account
		account = frappe.new_doc("IB Chart of Accounts")
		account.account_name = account_name
		account.account_type = "Receivable"
		account.root_type = "Asset"
		account.owner_type = "Customer"
		account.owner_name = self.customer_name
		account.is_group = 0
		
		# Add bank details
		if bank_details.get("bank_name"):
			account.bank_name = bank_details.get("bank_name")
			account.bank_account_number = bank_details.get("bank_account_number")
			account.ifsc_code = bank_details.get("ifsc_code")
		
		account.insert(ignore_permissions=True)
		
		return account.name
	
	def update_account_bank_details(self):
		"""Update bank details on the linked account"""
		if self.default_receivable_account and frappe.db.exists("IB Chart of Accounts", self.default_receivable_account):
			frappe.db.set_value("IB Chart of Accounts", self.default_receivable_account, {
				"bank_name": self.bank_name,
				"bank_account_number": self.bank_account_number,
				"ifsc_code": self.ifsc_code
			})
