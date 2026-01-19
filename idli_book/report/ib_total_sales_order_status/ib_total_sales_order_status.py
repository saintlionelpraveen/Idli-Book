# Copyright (c) 2024, Praveen and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 150},
		{"fieldname": "value", "label": "Total Amount", "fieldtype": "Currency", "width": 150}
	]
	
	data = frappe.db.sql("""
		SELECT 
			status, SUM(grand_total) as value
		FROM
			`tabIB Sales Order`
		GROUP BY
			status
		ORDER BY
			value DESC
	""", as_dict=True)
	
	# Prepare chart data
	chart = {
		"data": {
			"labels": [d.status for d in data],
			"datasets": [
				{
					"name": "Total Value",
					"values": [d.value for d in data]
				}
			]
		},
		"type": "bar",
		"height": 300,
		"colors": ["#ECAD4B", "#e74c3c", "#3498db", "#2ecc71", "#9b59b6"],
		"fieldtype": "Currency"
	}
	
	report_summary = []
	if data:
		total_value = sum([d.value for d in data])
		report_summary = [
			{"value": total_value, "label": "Total Sales Value", "datatype": "Currency", "currency": frappe.get_cached_value('Company',  frappe.defaults.get_user_default("Company"),  "default_currency") or "INR"}
		]

	return columns, data, None, chart, report_summary
