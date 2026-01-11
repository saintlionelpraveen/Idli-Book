# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{
			"fieldname": "total_sales_orders",
			"label": "Total Sales Orders",
			"fieldtype": "Int",
			"width": 150
		}
	]
	
	data = []
	
	# Count total sales orders
	count = frappe.db.count("IB Sales Order")
	
	data.append({
		"total_sales_orders": count
	})
	
	# Number card data format
	report_summary = [
		{
			"value": count,
			"label": "Total Sales Orders",
			"datatype": "Int",
		}
	]
	
	return columns, data, None, None, report_summary
