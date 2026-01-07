# Copyright (c) 2025, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def reset_chart_of_accounts():
	# 1. Delete GL Entries
	frappe.db.delete("IB GL Entry")
	
	# 2. Reset Org Defaults
	frappe.db.sql("""
		UPDATE `tabIB Organization` 
		SET default_receivable_account=NULL, default_payable_account=NULL, 
			default_income_account=NULL, default_expense_account=NULL
	""")
	
	# 3. Delete Accounts
	frappe.db.delete("IB Chart of Accounts")
	
	frappe.db.commit()
	return "Deleted All Accounts"

class IBOrganization(Document):
	pass
