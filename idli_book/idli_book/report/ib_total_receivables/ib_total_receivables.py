# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	Execute function for IB Total Receivables Script Report
	Returns columns and data showing ONLY total receivable amount
	"""
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Define report columns - Simple total amount only"""
	return [
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount Receivable"),
			"fieldtype": "Currency",
			"width": 200
		}
	]


def get_data(filters):
	"""Fetch total receivables from IB Sales Invoice"""
	conditions = get_conditions(filters)
	
	# Get total receivable amount
	query = f"""
		SELECT
			'Total Outstanding Receivable' as description,
			COALESCE(SUM(si.outstanding_amount), 0) as total_amount
		FROM `tabIB Sales Invoice` si
		WHERE si.docstatus = 1 
			AND si.outstanding_amount > 0
			AND si.invoice_date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}
	"""
	
	result = frappe.db.sql(query, filters, as_dict=1)
	
	# Return single row with total
	return result if result else [{"description": "Total Outstanding Receivable", "total_amount": 0}]


def get_conditions(filters):
	"""Build additional WHERE conditions based on filters"""
	conditions = []
	
	if filters.get("customer"):
		conditions.append("AND si.customer = %(customer)s")
	
	return " ".join(conditions) if conditions else ""
