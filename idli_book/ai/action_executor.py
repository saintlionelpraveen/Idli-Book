# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

"""
Action Executor - Execute Frappe queries based on classified intent
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, add_days

class ActionExecutor:
	"""Execute actions based on user intent"""
	
	@staticmethod
	def execute(function_name, arguments):
		"""Route to appropriate function"""
		
		# Map function names to methods
		function_map = {
			"get_customers": ActionExecutor.get_customers,
			"get_invoices": ActionExecutor.get_invoices,
			"get_payments": ActionExecutor.get_payments,
			"get_reports": ActionExecutor.get_reports,
			"get_summary": ActionExecutor.get_summary
		}
		
		if function_name not in function_map:
			return {"error": f"Unknown function: {function_name}"}
		
		try:
			return function_map[function_name](**arguments)
		except Exception as e:
			frappe.log_error(f"Action Executor Error: {str(e)}")
			return {"error": str(e)}
	
	@staticmethod
	def get_customers(limit=10, search=None):
		"""Get customer list"""
		filters = {}
		if search:
			filters["customer_name"] = ["like", f"%{search}%"]
		
		customers = frappe.get_all(
			"IB Customer",
			filters=filters,
			fields=["name", "customer_name", "email", "phone", "city"],
			limit=limit
		)
		
		return {
			"success": True,
			"data": customers,
			"message": f"Found {len(customers)} customers"
		}
	
	@staticmethod
	def get_invoices(status=None, customer=None, from_date=None, to_date=None, limit=10):
		"""Get sales invoices"""
		filters = {}
		
		if status:
			filters["status"] = status
		if customer:
			filters["customer"] = customer
		if from_date:
			filters["invoice_date"] = [">=", from_date]
		if to_date:
			if "invoice_date" in filters:
				filters["invoice_date"] = ["between", [from_date, to_date]]
			else:
				filters["invoice_date"] = ["<=", to_date]
		
		invoices = frappe.get_all(
			"IB Sales Invoice",
			filters=filters,
			fields=[
				"name", "customer", "invoice_date", "grand_total",
				"outstanding_amount", "status"
			],
			order_by="invoice_date desc",
			limit=limit
		)
		
		total_outstanding = sum(flt(inv.outstanding_amount) for inv in invoices)
		
		return {
			"success": True,
			"data": invoices,
			"summary": {
				"count": len(invoices),
				"total_outstanding": total_outstanding
			},
			"message": f"Found {len(invoices)} invoices"
		}
	
	@staticmethod
	def get_payments(from_date=None, to_date=None, payment_type=None, limit=10):
		"""Get payment entries"""
		filters = {}
		
		if payment_type:
			filters["payment_type"] = payment_type
		if from_date:
			filters["payment_date"] = [">=", from_date]
		if to_date:
			if "payment_date" in filters:
				filters["payment_date"] = ["between", [from_date, to_date]]
			else:
				filters["payment_date"] = ["<=", to_date]
		
		payments = frappe.get_all(
			"IB Payment",
			filters=filters,
			fields=[
				"name", "party_type", "party", "payment_date",
				"amount", "mode_of_payment"
			],
			order_by="payment_date desc",
			limit=limit
		)
		
		total_amount = sum(flt(p.amount) for p in payments)
		
		return {
			"success": True,
			"data": payments,
			"summary": {
				"count": len(payments),
				"total_amount": total_amount
			},
			"message": f"Found {len(payments)} payments"
		}
	
	@staticmethod
	def get_reports(report_name, filters=None):
		"""Run a report"""
		# Placeholder for report execution
		return {
			"success": True,
			"message": f"Report '{report_name}' execution coming soon"
		}
	
	@staticmethod
	def get_summary(metric):
		"""Get business summary metrics"""
		metrics = {
			"total_customers": frappe.db.count("IB Customer"),
			"total_vendors": frappe.db.count("IB Vendor"),
			"total_items": frappe.db.count("IB Item"),
			"unpaid_invoices": frappe.db.count("IB Sales Invoice", {"status": "Unpaid"}),
			"total_receivables": frappe.db.sql("""
				SELECT SUM(outstanding_amount) 
				FROM `tabIB Sales Invoice` 
				WHERE docstatus = 1
			""")[0][0] or 0,
			"total_payables": frappe.db.sql("""
				SELECT SUM(outstanding_amount) 
				FROM `tabIB Purchase Bill` 
				WHERE docstatus = 1
			""")[0][0] or 0
		}
		
		if metric == "all":
			return {
				"success": True,
				"data": metrics,
				"message": "Business summary"
			}
		elif metric in metrics:
			return {
				"success": True,
				"data": {metric: metrics[metric]},
				"message": f"{metric}: {metrics[metric]}"
			}
		else:
			return {
				"error": f"Unknown metric: {metric}"
			}

	@staticmethod
	def get_available_functions():
		"""Return function definitions for LLM (OpenAI 1.0+ format)"""
		return [
			{
				"name": "get_customers",
				"description": "Get list of customers",
				"parameters": {
					"type": "object",
					"properties": {
						"limit": {
							"type": "number",
							"description": "Maximum number of results"
						},
						"search": {
							"type": "string",
							"description": "Search by customer name"
						}
					}
				}
			},
			{
				"name": "get_invoices",
				"description": "Get sales invoices",
				"parameters": {
					"type": "object",
					"properties": {
						"status": {
							"type": "string",
							"enum": ["Draft", "Submitted", "Paid", "Unpaid", "Partially Paid"],
							"description": "Invoice status"
						},
						"customer": {
							"type": "string",
							"description": "Filter by customer name"
						},
						"from_date": {
							"type": "string",
							"description": "Start date (YYYY-MM-DD)"
						},
						"to_date": {
							"type": "string",
							"description": "End date (YYYY-MM-DD)"
						},
						"limit": {
							"type": "number",
							"description": "Maximum results"
						}
					}
				}
			},
			{
				"name": "get_payments",
				"description": "Get payment entries",
				"parameters": {
					"type": "object",
					"properties": {
						"from_date": {
							"type": "string",
							"description": "Start date"
						},
						"to_date": {
							"type": "string",
							"description": "End date"
						},
						"payment_type": {
							"type": "string",
							"enum": ["Receive", "Pay"],
							"description": "Payment type"
						}
					}
				}
			},
			{
				"name": "get_summary",
				"description": "Get business summary metrics",
				"parameters": {
					"type": "object",
					"properties": {
						"metric": {
							"type": "string",
							"enum": ["all", "total_customers", "total_vendors", "total_receivables", "total_payables"],
							"description": "Which metric to retrieve"
						}
					},
					"required": ["metric"]
				}
			}
		]
