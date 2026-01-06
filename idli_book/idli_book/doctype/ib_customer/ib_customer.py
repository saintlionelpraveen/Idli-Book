import frappe
from frappe.model.document import Document

class IBCustomer(Document):
	def validate(self):
		# Auto-create receivable account if not set
		if not self.default_receivable_account:
			self.default_receivable_account = self.create_receivable_account()
	
	def create_receivable_account(self):
		"""Create a receivable account for this customer"""
		account_name = f"Customer - {self.customer_name}"
		
		# Check if account already exists
		existing = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_name})
		if existing:
			return existing
		
		# Create new account
		account = frappe.get_doc({
			"doctype": "IB Chart of Accounts",
			"account_name": account_name,
			"account_type": "Receivable",
			"root_type": "Asset",
			"is_group": 0
		})
		account.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return account.name
