# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Vendor Payment Status Report
	Shows total amount paid vs. amount owed to vendors
	"""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
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
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 200
		}
	]


def get_data(filters):
	"""Fetch total paid and total owed amounts"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if not from_date or not to_date:
		return []
	
	# Get total amount paid to vendors
	paid_query = """
		SELECT COALESCE(SUM(amount), 0) as total_paid
		FROM `tabIB Payment`
		WHERE payment_type = 'Pay'
			AND docstatus = 1
			AND payment_date BETWEEN %(from_date)s AND %(to_date)s
	"""
	
	paid_result = frappe.db.sql(paid_query, {"from_date": from_date, "to_date": to_date}, as_dict=1)
	total_paid = paid_result[0].get("total_paid", 0) if paid_result else 0
	
	# Get total amount owed to vendors (outstanding bills)
	owed_query = """
		SELECT COALESCE(SUM(outstanding_amount), 0) as total_owed
		FROM `tabIB Purchase Bill`
		WHERE docstatus = 1
			AND outstanding_amount > 0
			AND bill_date BETWEEN %(from_date)s AND %(to_date)s
	"""
	
	owed_result = frappe.db.sql(owed_query, {"from_date": from_date, "to_date": to_date}, as_dict=1)
	total_owed = owed_result[0].get("total_owed", 0) if owed_result else 0
	
	return [
		{
			"description": "Total Amount Paid",
			"amount": total_paid
		},
		{
			"description": "Total Amount Owed",
			"amount": total_owed
		}
	]


def get_chart_data(data):
	"""Return chart data for paid vs owed comparison"""
	if not data or len(data) < 2:
		return None
	
	return {
		"data": {
			"labels": ["Amount Paid", "Amount Owed"],
			"datasets": [
				{
					"name": "Vendor Payments",
					"values": [
						data[0].get("amount", 0),
						data[1].get("amount", 0)
					]
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745", "#dc3545"]
	}
