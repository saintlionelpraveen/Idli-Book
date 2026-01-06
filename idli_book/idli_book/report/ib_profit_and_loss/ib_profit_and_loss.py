import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"fieldname": "account", "label": _("Account"), "fieldtype": "Link", "options": "IB Chart of Accounts", "width": 250},
		{"fieldname": "balance", "label": _("Balance"), "fieldtype": "Currency", "width": 120}
	]
	
	data = []
	
	# Fetch Income and Expense accounts
	# GL Entries aggregation
	
	gl_entries = frappe.db.sql("""
		SELECT account, SUM(credit) - SUM(debit) as balance
		FROM `tabIB GL Entry`
		WHERE posting_date BETWEEN %s AND %s
		GROUP BY account
	""", (filters.get("from_date"), filters.get("to_date")), as_dict=True)
	
	gl_map = {d.account: d.balance for d in gl_entries}
	
	accounts = frappe.get_all("IB Chart of Accounts", 
		filters={"root_type": ["in", ["Income", "Expense"]]}, 
		fields=["name", "root_type", "parent_account", "is_group"], 
		order_by="root_type desc, name") # Income first ideally
	
	total_income = 0
	total_expense = 0
	
	data.append({"account": "<b>Income</b>", "balance": ""})
	for acct in accounts:
		if acct.root_type == "Income":
			bal = gl_map.get(acct.name, 0)
			if bal != 0:
				data.append({"account": acct.name, "balance": bal})
				total_income += bal
				
	data.append({"account": "<b>Total Income</b>", "balance": total_income})
	data.append({"account": "", "balance": ""}) # Spacer
	
	data.append({"account": "<b>Expense</b>", "balance": ""})
	for acct in accounts:
		if acct.root_type == "Expense":
			# Expense usually Dr balance, so Cr - Dr is negative.
			# we want to show it as positive number usually, or keep sign.
			# P&L: Income - Expense.
			# Let's show positive for expense line items if they are debits.
			bal = gl_map.get(acct.name, 0)
			if bal != 0:
				# Bal is Cr - Dr. If expense, Dr > Cr, so bal is negative.
				val = -bal
				data.append({"account": acct.name, "balance": val})
				total_expense += val
				
	data.append({"account": "<b>Total Expense</b>", "balance": total_expense})
	
	net_profit = total_income - total_expense
	data.append({"account": "", "balance": ""})
	data.append({"account": "<b>Net Profit</b>", "balance": net_profit})
		
	return columns, data
