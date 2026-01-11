# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Low Stock Items Report
	Shows count of items below reorder level
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
			"label": _("Low Stock Items"),
			"fieldtype": "Int",
			"width": 150
		}
	]


def get_data(filters):
	"""Fetch count of low stock items"""
	
	# Get count of items where stock_quantity < reorder_level
	query = """
		SELECT COUNT(*) as low_stock_count
		FROM `tabIB Item`
		WHERE track_inventory = 1
			AND COALESCE(stock_quantity, 0) < COALESCE(reorder_level, 0)
			AND COALESCE(reorder_level, 0) > 0
	"""
	
	result = frappe.db.sql(query, as_dict=1)
	low_stock_count = result[0].get("low_stock_count", 0) if result else 0
	
	return [
		{
			"description": "Low Stock Items",
			"total_count": low_stock_count
		}
	]
