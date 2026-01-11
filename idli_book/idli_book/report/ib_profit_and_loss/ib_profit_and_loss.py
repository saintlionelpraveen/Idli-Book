# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	Enhanced Profit and Loss Report
	Production-ready with chart support
	"""
	if not filters:
		filters = {}
	
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(filters)
	
	return columns, data, None, chart


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "IB Chart of Accounts",
			"width": 300
		},
		{
			"fieldname": "balance",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 150
		}
	]


def get_data(filters):
	"""Fetch and format P&L data"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	company = filters.get("company")
	
	if not from_date or not to_date:
		return []
	
	# Fetch GL entries (excluding cancelled)
	conditions = "gl.is_cancelled = 0"
	
	gl_query = f"""
		SELECT 
			gl.account,
			SUM(gl.credit) - SUM(gl.debit) as balance
		FROM `tabIB GL Entry` gl
		WHERE gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND {conditions}
		GROUP BY gl.account
	"""
	
	gl_entries = frappe.db.sql(gl_query, {"from_date": from_date, "to_date": to_date}, as_dict=True)
	gl_map = {d.account: d.balance for d in gl_entries}
	
	# Fetch Income and Expense accounts
	accounts = frappe.get_all(
		"IB Chart of Accounts",
		filters={"root_type": ["in", ["Income", "Expense"]]},
		fields=["name", "root_type", "parent_account", "is_group"],
		order_by="root_type desc, name"
	)
	
	data = []
	total_income = 0
	total_expense = 0
	
	# Income Section
	data.append({
		"account": _("<b>INCOME</b>"),
		"balance": 0,
		"indent": 0
	})
	
	for acct in accounts:
		if acct.root_type == "Income":
			bal = gl_map.get(acct.name, 0)
			if bal != 0:
				data.append({
					"account": acct.name,
					"balance": bal,
					"indent": 1
				})
				total_income += bal
	
	data.append({
		"account": _("<b>Total Income</b>"),
		"balance": total_income,
		"indent": 0
	})
	
	# Spacer
	data.append({"account": "", "balance": 0})
	
	# Expense Section
	data.append({
		"account": _("<b>EXPENSES</b>"),
		"balance": 0,
		"indent": 0
	})
	
	for acct in accounts:
		if acct.root_type == "Expense":
			bal = gl_map.get(acct.name, 0)
			if bal != 0:
				# Convert to positive (expenses are typically debits, so balance is negative)
				val = abs(bal)
				data.append({
					"account": acct.name,
					"balance": val,
					"indent": 1
				})
				total_expense += val
	
	data.append({
		"account": _("<b>Total Expenses</b>"),
		"balance": total_expense,
		"indent": 0
	})
	
	# Net Profit/Loss
	net_profit = total_income - total_expense
	data.append({"account": "", "balance": 0})
	data.append({
		"account": _("<b>NET PROFIT/LOSS</b>"),
		"balance": net_profit,
		"indent": 0
	})
	
	return data


def get_chart_data(filters):
	"""Return chart data for dashboard"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if not from_date or not to_date:
		return None
	
	# Fetch totals for chart
	gl_query = """
		SELECT 
			acc.root_type,
			SUM(gl.credit) - SUM(gl.debit) as balance
		FROM `tabIB GL Entry` gl
		INNER JOIN `tabIB Chart of Accounts` acc ON gl.account = acc.name
		WHERE gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gl.is_cancelled = 0
			AND acc.root_type IN ('Income', 'Expense')
		GROUP BY acc.root_type
	"""
	
	results = frappe.db.sql(gl_query, {"from_date": from_date, "to_date": to_date}, as_dict=True)
	
	total_income = 0
	total_expense = 0
	
	for row in results:
		if row.root_type == "Income":
			total_income = row.balance
		elif row.root_type == "Expense":
			total_expense = abs(row.balance)
	
	net_profit = total_income - total_expense
	
	return {
		"data": {
			"labels": ["Income", "Expenses", "Net Profit"],
			"datasets": [
				{
					"name": "Amount",
					"values": [total_income, total_expense, net_profit]
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745", "#dc3545", "#007bff"]
	}
