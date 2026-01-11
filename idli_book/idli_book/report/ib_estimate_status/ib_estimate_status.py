# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "count",
			"label": _("Count"),
			"fieldtype": "Int",
			"width": 100
		}
	]
	
	# Group Estimates by Status
	sql = """
		SELECT status, COUNT(name) as count
		FROM `tabIB Estimate`
		GROUP BY status
	"""
	
	result = frappe.db.sql(sql, as_dict=True)
	
	data = result
	
	chart = {
		"data": {
			"labels": [d.get("status") for d in data],
			"datasets": [
				{
					"name": "Count",
					"values": [d.get("count") for d in data]
				}
			]
		},
		"type": "donut",
	}
	
	return columns, data, None, chart
