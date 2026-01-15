# Copyright (c) 2024, Idli Book and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	Execute function for IB Total Amount Payable Script Report
	Returns columns and data showing ONLY total payable amount
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
			"label": _("Total Amount Payable"),
			"fieldtype": "Currency",
			"width": 200
		}
	]


def get_data(filters):
	"""Fetch total payables from IB Purchase Bill"""
	conditions = get_conditions(filters)
	
	# Get total payable amount
	query = f"""
		SELECT
			'Total Outstanding Payable' as description,
			COALESCE(SUM(pb.outstanding_amount), 0) as total_amount
		FROM `tabIB Purchase Bill` pb
		WHERE pb.docstatus = 1 
			AND pb.outstanding_amount > 0
			{conditions}
	"""
	
	result = frappe.db.sql(query, filters, as_dict=1)
	
	# Return single row with total
	return result if result else [{"description": "Total Outstanding Payable", "total_amount": 0}]


def get_conditions(filters):
	"""Build additional WHERE conditions based on filters"""
	conditions = []
	
	if filters.get("vendor"):
		conditions.append("AND pb.vendor = %(vendor)s")
	
	return " ".join(conditions) if conditions else ""
