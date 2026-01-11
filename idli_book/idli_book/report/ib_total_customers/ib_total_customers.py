# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{
			"fieldname": "total_customers",
			"label": "Total Customers",
			"fieldtype": "Int",
			"width": 150
		}
	]
	
	data = []
	
	# Count total customers
	count = frappe.db.count("IB Customer")
	
	data.append({
		"total_customers": count
	})
	
	# Number card data format
	report_summary = [
		{
			"value": count,
			"label": "Total Customers",
			"datatype": "Int",
		}
	]
	
	return columns, data, None, None, report_summary
