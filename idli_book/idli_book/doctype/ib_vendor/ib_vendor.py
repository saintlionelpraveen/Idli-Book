# Copyright (c) 2025, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IBVendor(Document):
	"""
	IB Vendor Doctype Controller
	
	Auto-creates payable account in IB Chart of Accounts with naming:
	'Vendor - {Vendor Name} - Payable'
	"""
	
	def before_save(self):
		"""Create linked account if not already set"""
		if not self.default_payable_account:
			self.default_payable_account = self.create_payable_account()
		else:
			# Update bank details on existing account
			self.update_account_bank_details()
	
	def create_payable_account(self):
		"""Create a payable account for this vendor"""
		account_name = f"Vendor - {self.vendor_name} - Payable"
		
		# Check if account already exists
		if frappe.db.exists("IB Chart of Accounts", account_name):
			return account_name
		
		# Bank details from vendor
		bank_details = {
			"bank_name": self.bank_name,
			"bank_account_number": self.bank_account_number,
			"ifsc_code": self.ifsc_code
		}
		
		# Create new account
		account = frappe.new_doc("IB Chart of Accounts")
		account.account_name = account_name
		account.account_type = "Payable"
		account.root_type = "Liability"
		account.owner_type = "Vendor"
		account.owner_name = self.vendor_name
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
		if self.default_payable_account and frappe.db.exists("IB Chart of Accounts", self.default_payable_account):
			frappe.db.set_value("IB Chart of Accounts", self.default_payable_account, {
				"bank_name": self.bank_name,
				"bank_account_number": self.bank_account_number,
				"ifsc_code": self.ifsc_code
			})
