import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"fieldname": "account", "label": _("Account"), "fieldtype": "Link", "options": "IB Chart of Accounts", "width": 250},
		{"fieldname": "debit", "label": _("Debit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "credit", "label": _("Credit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "balance", "label": _("Balance"), "fieldtype": "Currency", "width": 120}
	]
	
	data = []
	
	# Fetch Asset, Liability, Equity accounts
	roots = frappe.get_all("IB Chart of Accounts", 
		filters={"root_type": ["in", ["Asset", "Liability", "Equity"]], "is_group": 1, "parent_account": ""}, 
		order_by="root_type")
		
	# Logic: Recursive tree traversal or simple grouping for now.
	# Let's do a simple aggregation query from GL Entry.
	
	# Fetch all GL Entries summed by Account
	gl_entries = frappe.db.sql("""
		SELECT account, SUM(debit) as debit, SUM(credit) as credit
		FROM `tabIB GL Entry`
		WHERE posting_date <= %s
		GROUP BY account
	""", (filters.get("to_date")), as_dict=True)
	
	gl_map = {d.account: d for d in gl_entries}
	
	total_asset = 0
	total_liability = 0
	total_equity = 0
	
	# Helper to build tree
	def get_account_balance(account_name):
		# This handles non-group accounts directly from GL
		bal = gl_map.get(account_name, {"debit": 0, "credit": 0})
		# Asset/Exp: Dr - Cr. Liab/Inc/Eq: Cr - Dr.
		# Balance Sheet usually shows standard Dr/Cr columns or Net.
		# Let's show Net.
		return bal
		
	# ... (Simplified implementation: List all accounts with non-zero balance)
	# Production ready: Should traverse tree.
	
	accounts = frappe.get_all("IB Chart of Accounts", fields=["name", "root_type", "parent_account", "is_group"], order_by="root_type, name")
	
	for acct in accounts:
		bal = get_account_balance(acct.name)
		net = bal['debit'] - bal['credit']
		
		# Skip zero balance for non-groups
		if net == 0 and not acct.is_group:
			continue
			
		data.append({
			"account": acct.name,
			"debit": bal['debit'],
			"credit": bal['credit'],
			"balance": net,
			"indent": 0 # TODO: Calculate indent based on tree depth
		})
		
	return columns, data
