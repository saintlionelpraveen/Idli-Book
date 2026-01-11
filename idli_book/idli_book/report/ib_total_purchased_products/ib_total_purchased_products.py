# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Total Purchased Products Report
	Shows count of unique purchased products
	"""
	columns = get_columns()
	data = get_data(filters)
	
	return columns, data


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
			"fieldname": "total_count",
			"label": _("Unique Products Purchased"),
			"fieldtype": "Int",
			"width": 200
		}
	]


def get_data(filters):
	"""Fetch count of unique purchased products"""
	
	# Count distinct items from submitted purchase bills
	query = """
		SELECT COUNT(DISTINCT item.item) as product_count
		FROM `tabIB Purchase Item` item
		INNER JOIN `tabIB Purchase Bill` bill ON item.parent = bill.name
		WHERE bill.docstatus = 1
	"""
	
	result = frappe.db.sql(query, as_dict=1)
	product_count = result[0].get("product_count", 0) if result else 0
	
	return [
		{
			"description": "Total Purchased Products",
			"total_count": product_count
		}
	]
