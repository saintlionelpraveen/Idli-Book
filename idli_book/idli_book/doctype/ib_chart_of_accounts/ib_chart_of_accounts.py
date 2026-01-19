# Copyright (c) 2025, You and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class IBChartofAccounts(NestedSet):
	nsm_parent_field = 'parent_account'
	
	def before_save(self):
		"""Set color indicator based on owner type"""
		if self.owner_type == "Organization":
			self.color_indicator = "Red"
		elif self.owner_type == "Customer":
			self.color_indicator = "Green"
		elif self.owner_type == "Vendor":
			self.color_indicator = "Yellow"
		else:
			self.color_indicator = ""
	
	def validate(self):
		"""Set root_type based on account_type if not set"""
		if not self.root_type and self.account_type:
			root_map = {
				"Receivable": "Asset",
				"Payable": "Liability",
				"Income": "Income",
				"Expense": "Expense",
				"Asset": "Asset",
				"Liability": "Liability",
				"Equity": "Equity",
				"Bank": "Asset",
				"Cash": "Asset"
			}
			self.root_type = root_map.get(self.account_type, "Asset")


def get_or_create_account(account_name, account_type, root_type, owner_type, owner_name, bank_details=None):
	"""
	Get existing account or create new one.
	Returns the account name (which is used as ID).
	"""
	# Check if account exists
	if frappe.db.exists("IB Chart of Accounts", account_name):
		return account_name
	
	# Create new account
	account = frappe.new_doc("IB Chart of Accounts")
	account.account_name = account_name
	account.account_type = account_type
	account.root_type = root_type
	account.owner_type = owner_type
	account.owner_name = owner_name
	account.is_group = 0
	
	# Add bank details if provided
	if bank_details:
		account.bank_name = bank_details.get("bank_name")
		account.bank_account_number = bank_details.get("bank_account_number")
		account.ifsc_code = bank_details.get("ifsc_code")
	
	account.insert(ignore_permissions=True)
	
	return account.name
