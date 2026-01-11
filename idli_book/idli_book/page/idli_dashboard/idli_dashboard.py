"""
Idli Dashboard API
Provides data for charts and metrics
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months, formatdate, nowdate
from datetime import datetime, timedelta

@frappe.whitelist()
def get_dashboard_data(period="This Month"):
	"""Get comprehensive dashboard data"""
	data = {
		"summary_cards": get_summary_cards(period),
		"cash_flow_chart": get_cash_flow_data(period),
		"income_vs_expense": get_income_expense_data(period),
		"top_customers": get_top_customers(period),
		"top_items": get_top_selling_items(period),
		"outstanding_summary": get_outstanding_summary(),
		"bank_balance": get_bank_balance(),
		"recent_transactions": get_recent_transactions()
	}
	return data

def get_summary_cards(period):
	"""Key metrics cards with counts"""
	filters = get_date_filters(period)
	
	# Use single query for revenue with count
	revenue_data = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(grand_total), 0) as total,
			COUNT(*) as count
		FROM `tabIB Sales Invoice`
		WHERE docstatus = 1
		AND invoice_date BETWEEN %s AND %s
	""", (filters['from_date'], filters['to_date']), as_dict=True)[0]
	
	# Use single query for expenses with count
	expenses_data = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(grand_total), 0) as total,
			COUNT(*) as count
		FROM `tabIB Purchase Bill`
		WHERE docstatus = 1
		AND bill_date BETWEEN %s AND %s
	""", (filters['from_date'], filters['to_date']), as_dict=True)[0]
	
	# Cash flow queries
	cash_in = frappe.db.sql("""
		SELECT COALESCE(SUM(amount), 0) as total
		FROM `tabIB Payment`
		WHERE docstatus = 1
		AND payment_type = 'Receive'
		AND payment_date BETWEEN %s AND %s
	""", (filters['from_date'], filters['to_date']), as_dict=True)[0]
	
	cash_out = frappe.db.sql("""
		SELECT COALESCE(SUM(amount), 0) as total
		FROM `tabIB Payment`
		WHERE docstatus = 1
		AND payment_type = 'Pay'
		AND payment_date BETWEEN %s AND %s
	""", (filters['from_date'], filters['to_date']), as_dict=True)[0]
	
	# Calculate profit
	profit = flt(revenue_data.total) - flt(expenses_data.total)
	
	return {
		"revenue": flt(revenue_data.total, 2),
		"invoice_count": revenue_data.count,
		"expenses": flt(expenses_data.total, 2),
		"bill_count": expenses_data.count,
		"profit": flt(profit, 2),
		"cash_in": flt(cash_in.total, 2),
		"cash_out": flt(cash_out.total, 2),
		"net_cash_flow": flt(cash_in.total - cash_out.total, 2)
	}

def get_cash_flow_data(period):
	"""Cash flow chart data (last 12 months)"""
	data = {"labels": [], "cash_in": [], "cash_out": []}
	
	for i in range(11, -1, -1):
		month_date = add_months(nowdate(), -i)
		month_start = getdate(month_date).replace(day=1)
		month_end = add_months(month_start, 1) - timedelta(days=1)
		
		# Cash In
		cash_in = frappe.db.sql("""
			SELECT COALESCE(SUM(amount), 0) as total
			FROM `tabIB Payment`
			WHERE docstatus = 1
			AND payment_type = 'Receive'
			AND payment_date BETWEEN %s AND %s
		""", (month_start, month_end))[0][0]
		
		# Cash Out
		cash_out = frappe.db.sql("""
			SELECT COALESCE(SUM(amount), 0) as total
			FROM `tabIB Payment`
			WHERE docstatus = 1
			AND payment_type = 'Pay'
			AND payment_date BETWEEN %s AND %s
		""", (month_start, month_end))[0][0]
		
		data["labels"].append(month_start.strftime("%b %Y"))
		data["cash_in"].append(flt(cash_in, 2))
		data["cash_out"].append(flt(cash_out, 2))
	
	return data

def get_income_expense_data(period):
	"""Income vs Expense comparison"""
	filters = get_date_filters(period)
	
	# Group by month for the period
	data = {"labels": [], "income": [], "expense": []}
	
	# Get start and end month
	start_date = getdate(filters['from_date'])
	end_date = getdate(filters['to_date'])
	
	current = start_date.replace(day=1)
	while current <= end_date:
		month_end = add_months(current, 1) - timedelta(days=1)
		
		# Income
		income = frappe.db.sql("""
			SELECT COALESCE(SUM(grand_total), 0)
			FROM `tabIB Sales Invoice`
			WHERE docstatus = 1
			AND invoice_date BETWEEN %s AND %s
		""", (current, month_end))[0][0]
		
		# Expense
		expense = frappe.db.sql("""
			SELECT COALESCE(SUM(grand_total), 0)
			FROM `tabIB Purchase Bill`
			WHERE docstatus = 1
			AND bill_date BETWEEN %s AND %s
		""", (current, month_end))[0][0]
		
		data["labels"].append(current.strftime("%b"))
		data["income"].append(flt(income, 2))
		data["expense"].append(flt(expense, 2))
		
		current = add_months(current, 1)
	
	return data

def get_top_customers(period, limit=5):
	"""Top customers by revenue"""
	filters = get_date_filters(period)
	
	customers = frappe.db.sql("""
		SELECT 
			customer,
			SUM(grand_total) as total_revenue,
			COUNT(*) as invoice_count
		FROM `tabIB Sales Invoice`
		WHERE docstatus = 1
		AND invoice_date BETWEEN %s AND %s
		GROUP BY customer
		ORDER BY total_revenue DESC
		LIMIT %s
	""", (filters['from_date'], filters['to_date'], limit), as_dict=True)
	
	return customers

def get_top_selling_items(period, limit=5):
	"""Top selling items"""
	filters = get_date_filters(period)
	
	items = frappe.db.sql("""
		SELECT 
			ii.item_code,
			ii.item_name,
			SUM(ii.quantity) as total_qty,
			SUM(ii.amount) as total_amount
		FROM `tabIB Invoice Item` ii
		INNER JOIN `tabIB Sales Invoice` si ON ii.parent = si.name
		WHERE si.docstatus = 1
		AND si.invoice_date BETWEEN %s AND %s
		GROUP BY ii.item_code
		ORDER BY total_amount DESC
		LIMIT %s
	""", (filters['from_date'], filters['to_date'], limit), as_dict=True)
	
	return items

def get_outstanding_summary():
	"""Outstanding receivables and payables with counts"""
	receivable_data = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(outstanding_amount), 0) as total,
			COUNT(*) as count
		FROM `tabIB Sales Invoice`
		WHERE docstatus = 1
		AND outstanding_amount > 0
	""", as_dict=True)[0]
	
	payable_data = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(outstanding_amount), 0) as total,
			COUNT(*) as count
		FROM `tabIB Purchase Bill`
		WHERE docstatus = 1
		AND outstanding_amount > 0
	""", as_dict=True)[0]
	
	return {
		"receivable": flt(receivable_data.total, 2),
		"receivable_count": receivable_data.count,
		"payable": flt(payable_data.total, 2),
		"payable_count": payable_data.count
	}

def get_bank_balance():
	"""Current bank/cash balance"""
	# Get all Bank and Cash accounts
	bank_balance = frappe.db.sql("""
		SELECT 
			account,
			SUM(debit - credit) as balance
		FROM `tabIB GL Entry`
		WHERE is_cancelled = 0
		AND account IN (
			SELECT account_name 
			FROM `tabIB Chart of Accounts`
			WHERE account_type IN ('Bank', 'Cash')
		)
		GROUP BY account
	""", as_dict=True)
	
	total = sum([flt(b.balance) for b in bank_balance])
	
	return {
		"total": flt(total, 2),
		"accounts": bank_balance
	}

def get_recent_transactions(limit=10):
	"""Recent transactions across all types"""
	transactions = []
	
	# Recent Invoices
	invoices = frappe.get_all("IB Sales Invoice",
		filters={"docstatus": 1},
		fields=["name", "customer", "invoice_date as date", "grand_total as amount", "'Sales Invoice' as type"],
		order_by="creation desc",
		limit=limit//2
	)
	transactions.extend(invoices)
	
	# Recent Payments
	payments = frappe.get_all("IB Payment",
		filters={"docstatus": 1},
		fields=["name", "party as customer", "payment_date as date", "amount", "payment_type as type"],
		order_by="creation desc",
		limit=limit//2
	)
	transactions.extend(payments)
	
	# Sort by date
	transactions = sorted(transactions, key=lambda x: x.date, reverse=True)[:limit]
	
	return transactions

def get_date_filters(period):
	"""Get date range based on period"""
	today = getdate(nowdate())
	
	if period == "Today":
		return {"from_date": today, "to_date": today}
	elif period == "This Week":
		start = today - timedelta(days=today.weekday())
		return {"from_date": start, "to_date": today}
	elif period == "This Month":
		start = today.replace(day=1)
		return {"from_date": start, "to_date": today}
	elif period == "This Quarter":
		quarter_start_month = ((today.month - 1) // 3) * 3 + 1
		start = today.replace(month=quarter_start_month, day=1)
		return {"from_date": start, "to_date": today}
	elif period == "This Year":
		start = today.replace(month=4, day=1)  # Indian FY starts April
		if today.month < 4:
			start = start.replace(year=today.year - 1)
		return {"from_date": start, "to_date": today}
	else:  # Last 30 Days
		start = today - timedelta(days=30)
		return {"from_date": start, "to_date": today}
