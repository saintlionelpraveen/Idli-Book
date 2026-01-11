# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{
			"fieldname": "total_estimates",
			"label": "Total Estimates",
			"fieldtype": "Int",
			"width": 150
		}
	]
	
	data = []
	
	# Count total estimates
	count = frappe.db.count("IB Estimate")
	
	data.append({
		"total_estimates": count
	})
	
	# Number card data format
	report_summary = [
		{
			"value": count,
			"label": "Total Estimates",
			"datatype": "Int",
		}
	]
	
	return columns, data, None, None, report_summary
