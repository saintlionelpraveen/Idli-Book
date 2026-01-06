"""
Setup utility to create default Chart of Accounts
"""
import frappe

def setup_default_accounts():
	"""Create default accounts for the organization"""
	
	accounts_to_create = [
		# Assets
		{
			"account_name": "Cash - Organization",
			"account_type": "Cash",
			"root_type": "Asset",
			"is_group": 0
		},
		{
			"account_name": "Bank - Organization",
			"account_type": "Bank",
			"root_type": "Asset",
			"is_group": 0
		},
		{
			"account_name": "Accounts Receivable - Organization",
			"account_type": "Receivable",
			"root_type": "Asset",
			"is_group": 0
		},
		
		# Liabilities
		{
			"account_name": "Accounts Payable - Organization",
			"account_type": "Payable",
			"root_type": "Liability",
			"is_group": 0
		},
		
		# Income
		{
			"account_name": "Sales Revenue - Organization",
			"account_type": "Income",
			"root_type": "Income",
			"is_group": 0
		},
		
		# Expenses
		{
			"account_name": "Purchase Expense - Organization",
			"account_type": "Expense",
			"root_type": "Expense",
			"is_group": 0
		},
		{
			"account_name": "Cost of Goods Sold - Organization",
			"account_type": "Expense",
			"root_type": "Expense",
			"is_group": 0
		},
		
		# Tax
		{
			"account_name": "GST Payable - Organization",
			"account_type": "Liability",
			"root_type": "Liability",
			"is_group": 0
		},
		{
			"account_name": "GST Receivable - Organization",
			"account_type": "Asset",
			"root_type": "Asset",
			"is_group": 0
		}
	]
	
	created_accounts = []
	
	for account_data in accounts_to_create:
		# Check if account already exists
		existing = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_data["account_name"]})
		
		if not existing:
			try:
				account = frappe.get_doc({
					"doctype": "IB Chart of Accounts",
					**account_data
				})
				account.insert(ignore_permissions=True)
				created_accounts.append(account_data["account_name"])
			except Exception as e:
				frappe.log_error(f"Error creating account {account_data['account_name']}: {str(e)}")
	
	frappe.db.commit()
	
	# Update organization defaults
	update_organization_defaults()
	
	return created_accounts

def update_organization_defaults():
	"""Set default accounts in organization"""
	org_name = "IB Organization"
	
	# Check if organization exists
	if not frappe.db.exists("IB Organization", org_name):
		return
	
	org = frappe.get_doc("IB Organization", org_name)
	
	# Set defaults if fields exist
	accounts_map = {
		"default_receivable_account": "Accounts Receivable - Organization",
		"default_payable_account": "Accounts Payable - Organization",
		"default_income_account": "Sales Revenue - Organization",
		"default_expense_account": "Purchase Expense - Organization",
		"default_tax_account": "GST Payable - Organization"
	}
	
	for field, account_name in accounts_map.items():
		if hasattr(org, field):
			account = frappe.db.get_value("IB Chart of Accounts", {"account_name": account_name})
			if account:
				setattr(org, field, account)
	
	org.save(ignore_permissions=True)
	frappe.db.commit()

@frappe.whitelist()
def run_setup():
	"""API endpoint to run setup"""
	created = setup_default_accounts()
	return {
		"success": True,
		"message": f"Created {len(created)} accounts",
		"accounts": created
	}
