# Copyright (c) 2024, Praveen and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 150},
		{"fieldname": "value", "label": "Count", "fieldtype": "Int", "width": 100}
	]
	
	data = frappe.db.sql("""
		SELECT 
			status, COUNT(name) as value
		FROM
			`tabIB Sales Order`
		GROUP BY
			status
	""", as_dict=True)
	
	chart = {
		"data": {
			"labels": [d.status for d in data],
			"datasets": [
				{
					"name": "Orders",
					"values": [d.value for d in data]
				}
			]
		},
		"type": "donut",
		"height": 300,
		"colors": ["#ECAD4B", "#3498db", "#e74c3c", "#2ecc71", "#9b59b6"]
	}
	
	report_summary = []
	if data:
		total_orders = sum([d.value for d in data])
		report_summary = [
			{"value": total_orders, "label": "Total Orders", "datatype": "Int", "currency": None}
		]

	return columns, data, None, chart, report_summary
