# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Total Expenses Report
	Shows total expenses from GL entries
	"""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(filters)
	
	return columns, data, None, chart


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Expenses"),
			"fieldtype": "Currency",
			"width": 200
		}
	]


def get_data(filters):
	"""Fetch total expenses from GL entries"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if not from_date or not to_date:
		return [{"description": "Total Expenses", "total_amount": 0}]
	
	# Get total expenses (debit - credit for expense accounts, shown as positive)
	query = """
		SELECT
			'Total Expenses' as description,
			COALESCE(ABS(SUM(gl.credit - gl.debit)), 0) as total_amount
		FROM `tabIB GL Entry` gl
		INNER JOIN `tabIB Chart of Accounts` acc ON gl.account = acc.name
		WHERE gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gl.is_cancelled = 0
			AND acc.root_type = 'Expense'
	"""
	
	result = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=1)
	
	return result if result else [{"description": "Total Expenses", "total_amount": 0}]


def get_chart_data(filters):
	"""Return chart data"""
	data = get_data(filters)
	total_expenses = data[0].get("total_amount", 0) if data else 0
	
	return {
		"data": {
			"labels": ["Total Expenses"],
			"datasets": [{"name": "Amount", "values": [total_expenses]}]
		},
		"type": "bar",
		"colors": ["#dc3545"]
	}
