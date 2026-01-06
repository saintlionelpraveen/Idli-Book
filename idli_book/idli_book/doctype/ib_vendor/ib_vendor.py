import frappe
from frappe.model.document import Document

class IBVendor(Document):
	def validate(self):
		# Auto-create payable account if not set
		if not self.default_payable_account:
			self.default_payable_account = self.create_payable_account()
	
	def create_payable_account(self):
		"""Create a payable account for this vendor"""
		account_name = f"Vendor - {self.vendor_name}"
		
		# Check if account already exists
		existing = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_name})
		if existing:
			return existing
		
		# Create new account
		account = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": account_name,
			"account_type": "Payable",
			"root_type": "Liability",
			"is_group": 0
		})
		account.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return account.name
