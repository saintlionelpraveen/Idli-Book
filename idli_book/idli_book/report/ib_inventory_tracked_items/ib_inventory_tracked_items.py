# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Inventory Tracked Items Report
	Shows count of items with inventory tracking enabled
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
			"label": _("Tracked Items"),
			"fieldtype": "Int",
			"width": 150
		}
	]


def get_data(filters):
	"""Fetch count of inventory-tracked items"""
	
	# Get count of items with track_inventory = 1
	tracked_count = frappe.db.count("IB Item", {"track_inventory": 1})
	
	return [
		{
			"description": "Inventory Tracked Items",
			"total_count": tracked_count
		}
	]
