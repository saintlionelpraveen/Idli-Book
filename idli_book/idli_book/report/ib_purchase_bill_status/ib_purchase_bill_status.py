# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Purchase Bill Status Report
	Shows breakdown of purchase bills by status - optimized for charts
	"""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
	return columns, data, None, chart


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "count",
			"label": _("Bill Count"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "percentage",
			"label": _("Percentage"),
			"fieldtype": "Percent",
			"width": 120
		}
	]


def get_data(filters):
	"""Fetch purchase bill status breakdown"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if not from_date or not to_date:
		return []
	
	# Get status breakdown
	query = """
		SELECT
			CASE 
				WHEN docstatus = 0 THEN 'Draft'
				WHEN docstatus = 2 THEN 'Cancelled'
				WHEN docstatus = 1 AND status = 'Paid' THEN 'Paid'
				WHEN docstatus = 1 AND status = 'Partially Paid' THEN 'Partially Paid'
				WHEN docstatus = 1 AND status = 'Overdue' THEN 'Overdue'
				WHEN docstatus = 1 THEN 'Awaiting Payment'
				ELSE 'Other'
			END as status,
			COUNT(*) as count,
			SUM(grand_total) as total_amount
		FROM `tabIB Purchase Bill`
		WHERE bill_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY 
			CASE 
				WHEN docstatus = 0 THEN 'Draft'
				WHEN docstatus = 2 THEN 'Cancelled'
				WHEN docstatus = 1 AND status = 'Paid' THEN 'Paid'
				WHEN docstatus = 1 AND status = 'Partially Paid' THEN 'Partially Paid'
				WHEN docstatus = 1 AND status = 'Overdue' THEN 'Overdue'
				WHEN docstatus = 1 THEN 'Awaiting Payment'
				ELSE 'Other'
			END
		ORDER BY count DESC
	"""
	
	result = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=1)
	
	# Calculate percentages
	total_count = sum([row.get("count", 0) for row in result])
	
	for row in result:
		row["percentage"] = (row.get("count", 0) / total_count * 100) if total_count > 0 else 0
	
	return result


def get_chart_data(data):
	"""Return chart data for status breakdown"""
	if not data:
		return None
	
	labels = [row.get("status", "") for row in data]
	values = [row.get("count", 0) for row in data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": "Bill Count", "values": values}]
		},
		"type": "pie",
		"colors": ["#28a745", "#ffc107", "#dc3545", "#17a2b8", "#6c757d", "#fd7e14"]
	}
