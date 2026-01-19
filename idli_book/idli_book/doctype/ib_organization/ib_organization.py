# Copyright (c) 2025, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IBOrganization(Document):
	def before_save(self):
		"""Create or update linked accounts in IB Chart of Accounts"""
		org_name = self.organization_name or "Organization"
		
		# Bank details for Bank account
		bank_details = {
			"bank_name": self.bank_name,
			"bank_account_number": self.bank_account_number,
			"ifsc_code": self.ifsc_code
		}
		
		# Create/get accounts with proper naming
		account_configs = [
			("default_receivable_account", f"{org_name} - Accounts Receivable", "Receivable", "Asset"),
			("default_payable_account", f"{org_name} - Accounts Payable", "Payable", "Liability"),
			("default_income_account", f"{org_name} - Sales Income", "Income", "Income"),
			("default_expense_account", f"{org_name} - Operating Expenses", "Expense", "Expense"),
			("default_bank_account", f"{org_name} - Bank", "Bank", "Asset"),
			("default_cash_account", f"{org_name} - Cash", "Cash", "Asset"),
			("gst_output_account", f"{org_name} - GST Payable", "Liability", "Liability"),
			("gst_input_account", f"{org_name} - GST Input Credit", "Asset", "Asset"),
			("discount_account", f"{org_name} - Discount Given", "Expense", "Expense"),
			("round_off_account", f"{org_name} - Round Off", "Expense", "Expense"),
		]
		
		for field_name, account_name, account_type, root_type in account_configs:
			current_value = getattr(self, field_name, None)
			
			# Only create if not already set
			if not current_value:
				account = self.get_or_create_account(
					account_name, 
					account_type, 
					root_type, 
					org_name,
					bank_details if account_type == "Bank" else None
				)
				setattr(self, field_name, account)
	
	def get_or_create_account(self, account_name, account_type, root_type, owner_name, bank_details=None):
		"""Get existing account or create new one"""
		# Check if account exists
		if frappe.db.exists("IB Chart of Accounts", account_name):
			# Update bank details if this is bank account
			if bank_details and account_type == "Bank":
				frappe.db.set_value("IB Chart of Accounts", account_name, {
					"bank_name": bank_details.get("bank_name"),
					"bank_account_number": bank_details.get("bank_account_number"),
					"ifsc_code": bank_details.get("ifsc_code")
				})
			return account_name
		
		# Create new account
		account = frappe.new_doc("IB Chart of Accounts")
		account.account_name = account_name
		account.account_type = account_type
		account.root_type = root_type
		account.owner_type = "Organization"
		account.owner_name = owner_name
		account.is_group = 0
		
		# Add bank details if provided
		if bank_details:
			account.bank_name = bank_details.get("bank_name")
			account.bank_account_number = bank_details.get("bank_account_number")
			account.ifsc_code = bank_details.get("ifsc_code")
		
		account.insert(ignore_permissions=True)
		
		return account.name


@frappe.whitelist()
def reset_account_defaults():
	"""Reset all account fields and recreate accounts"""
	if frappe.db.exists("IB Organization", "IB Organization"):
		org = frappe.get_doc("IB Organization", "IB Organization")
		
		# Clear all account links
		org.default_receivable_account = None
		org.default_payable_account = None
		org.default_income_account = None
		org.default_expense_account = None
		org.default_bank_account = None
		org.default_cash_account = None
		org.gst_output_account = None
		org.gst_input_account = None
		org.discount_account = None
		org.round_off_account = None
		
		# Save will trigger before_save hook to recreate accounts
		org.save(ignore_permissions=True)
		
		return "Account defaults have been reset and recreated"
	
	return "Organization not found"
