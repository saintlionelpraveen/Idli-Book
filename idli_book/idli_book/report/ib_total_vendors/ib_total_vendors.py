# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	IB Total Vendors Report
	Shows total count of vendors
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
			"label": _("Total Vendors"),
			"fieldtype": "Int",
			"width": 150
		}
	]


def get_data(filters):
	"""Fetch total count of vendors"""
	
	total_vendors = frappe.db.count("IB Vendor")
	
	return [
		{
			"description": "Total Vendors",
			"total_count": total_vendors
		}
	]
