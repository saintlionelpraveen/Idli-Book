# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Top 5 Expenses Report
	Shows top 5 items by total purchase amount
	"""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	
	return columns, data, None, chart


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "item",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "IB Item",
			"width": 180
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount Purchased"),
			"fieldtype": "Currency",
			"width": 180
		},
		{
			"fieldname": "total_qty",
			"label": _("Total Quantity"),
			"fieldtype": "Float",
			"width": 120
		}
	]


def get_data(filters):
	"""Fetch top 5 items by purchase amount"""
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if not from_date or not to_date:
		return []
	
	# Get top 5 items by total purchase amount
	query = """
		SELECT
			item.item,
			item.item_name,
			SUM(item.amount) as total_amount,
			SUM(item.qty) as total_qty
		FROM `tabIB Purchase Item` item
		INNER JOIN `tabIB Purchase Bill` bill ON item.parent = bill.name
		WHERE bill.docstatus = 1
			AND bill.bill_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY item.item, item.item_name
		ORDER BY SUM(item.amount) DESC
		LIMIT 5
	"""
	
	return frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=1)


def get_chart_data(data):
	"""Return chart data for top 5 expenses"""
	if not data:
		return None
	
	labels = [row.get("item_name", row.get("item", "")) for row in data]
	values = [row.get("total_amount", 0) for row in data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": "Amount Purchased", "values": values}]
		},
		"type": "bar",
		"colors": ["#dc3545"]
	}
