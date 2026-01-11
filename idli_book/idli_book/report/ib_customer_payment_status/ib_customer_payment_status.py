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
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 150
		}
	]
	
	if not filters:
		filters = {}

	# Default to current fiscal year if not provided (optional, but good practice)
	# For "Total status" we might want all time unless filtered.
	
	# 1. Total Received Amount
	# Sum of all received payments (submitted)
	received_sql = """
		SELECT SUM(amount) as total_received
		FROM `tabIB Payment`
		WHERE payment_type = 'Receive' AND docstatus = 1
	"""
	received_result = frappe.db.sql(received_sql, as_dict=1)
	total_received = received_result[0].get("total_received") or 0
	
	# 2. Total Outstanding Amount
	# Sum of outstanding amount from all submitted Sales Invoices
	outstanding_sql = """
		SELECT SUM(outstanding_amount) as total_outstanding
		FROM `tabIB Sales Invoice`
		WHERE docstatus = 1
	"""
	outstanding_result = frappe.db.sql(outstanding_sql, as_dict=1)
	total_outstanding = outstanding_result[0].get("total_outstanding") or 0
	
	data = [
		{"status": "Received", "amount": total_received},
		{"status": "Outstanding", "amount": total_outstanding}
	]
	
	# Chart Data
	chart = {
		"data": {
			"labels": ["Received", "Outstanding"],
			"datasets": [
				{
					"name": "Amount",
					"values": [total_received, total_outstanding]
				}
			]
		},
		"type": "bar",
		"colors": ["#48bb78", "#f56565"] # Green for Received, Red for Outstanding
	}
	
	return columns, data, None, chart
