# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [
		{
			"fieldname": "item_name",
			"label": "Best Selling Product",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "total_revenue",
			"label": "Total Revenue",
			"fieldtype": "Currency",
			"width": 150
		}
	]
	
	# Query to get best selling product based on total revenue amount in submitted Sales Invoices
	# We join Sales Invoice and Invoice Item to ensure we only count submitted invoices
	sql = """
		SELECT 
			ii.item_name, 
			SUM(ii.amount) as total_revenue
		FROM `tabIB Sales Invoice` si
		JOIN `tabIB Invoice Item` ii ON ii.parent = si.name
		WHERE si.docstatus = 1
		GROUP BY ii.item_name
		ORDER BY total_revenue DESC
		LIMIT 1
	"""
	
	result = frappe.db.sql(sql, as_dict=True)
	
	data = []
	report_summary = []
	
	if result:
		best_item = result[0]
		data.append(best_item)
		
		# For number card, we want to show the ITEM NAME as the main value
		report_summary = [
			{
				"value": str(best_item.get("item_name")),
				"label": "Best Selling Product",
				"datatype": "Data",
				"currency": None
			}
		]
	else:
		data.append({"item_name": "No Sales Yet", "total_revenue": 0})
		report_summary = [
			{
				"value": "N/A",
				"label": "Best Selling Product", 
				"datatype": "Data",
				"currency": None
			}
		]
	
	return columns, data, None, None, report_summary
