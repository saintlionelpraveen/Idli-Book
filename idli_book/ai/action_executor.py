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
			"get_table_list": ActionExecutor.get_table_list,
			"get_record_details": ActionExecutor.get_record_details,
			"get_summary": ActionExecutor.get_summary,
            # Legacy/Specific helpers can remain if needed, or be deprecated
            "get_customers": ActionExecutor.get_customers,
			"get_invoices": ActionExecutor.get_invoices,
			"get_payments": ActionExecutor.get_payments,
		}
		
		if function_name not in function_map:
			return {"error": f"Unknown function: {function_name}"}
		
		try:
			return function_map[function_name](**arguments)
		except Exception as e:
			frappe.log_error(f"Action Executor Error: {str(e)}")
			return {"error": str(e)}

	@staticmethod
	def get_table_list(doctype, filters=None, search=None, limit=5, order_by=None):
		"""Generic function to list records from any DocType"""
		try:
			# Security: Ensure we only access IB DocTypes or allowed modules
			if not doctype.startswith("IB "):
				return {"error": "Access denied. Can only query 'IB' (Idli Book) DocTypes."}

			if not filters: filters = {}
			
			# Basic search implementation
			if search:
				# Try to find a 'name' or 'title' like field
				meta = frappe.get_meta(doctype)
				title_field = meta.title_field or "name"
				filters[title_field] = ["like", f"%{search}%"]

			fields = ["name"]
            # Try to fetch list_view fields if available, else standard fields
			meta = frappe.get_meta(doctype)
			if meta.title_field and meta.title_field != 'name':
				fields.append(meta.title_field)
            
			# Add some sensible defaults if not specified
			if "status" in [d.fieldname for d in meta.fields]:
				fields.append("status")
			if "grand_total" in [d.fieldname for d in meta.fields]:
				fields.append("grand_total")

			data = frappe.get_all(
				doctype,
				filters=filters,
				fields=fields,
				limit=limit,
				order_by=order_by or "modified desc"
			)
			
			return {
				"success": True,
				"data": data,
				"message": f"Found {len(data)} records in {doctype}"
			}
		except Exception as e:
			return {"error": str(e)}

	@staticmethod
	def get_record_details(doctype, name):
		"""Generic function to get full details of a record"""
		try:
			if not doctype.startswith("IB "):
				return {"error": "Access denied."}

			if not frappe.db.exists(doctype, name):
				return {"error": f"{doctype} '{name}' found."}
				
			doc = frappe.get_doc(doctype, name)
			return {
				"success": True,
				"data": doc.as_dict(),
				"message": f"Details for {name}"
			}
		except Exception as e:
			return {"error": str(e)}

	# ... (Keep existing specific methods for backwards compatibility or high-level summaries logic) ...
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
				"name": "get_table_list",
				"description": "Get a list of records for a specific Table/DocType. Use this to find names of documents/records.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"description": "Exact name of the DocType (e.g., 'IB Sales Invoice', 'IB Customer')"
						},
						"filters": {
							"type": "object",
							"description": "Dictionary of filters (e.g., {'status': 'Unpaid'})"
						},
						"search": {
							"type": "string",
							"description": "Search term for the name or title"
						},
                        "limit": { "type": "number" }
					},
					"required": ["doctype"]
				}
			},
			{
				"name": "get_record_details",
				"description": "Get valid details for a specific record.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": { "type": "string" },
						"name": { "type": "string", "description": "The ID/Name of the record (e.g. 'INV-001')" }
					},
					"required": ["doctype", "name"]
				}
			},
			# Keep summary as it's a useful aggregation
			{
				"name": "get_summary",
				"description": "Get business summary metrics (totals)",
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
