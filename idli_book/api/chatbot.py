# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

"""
Chatbot API Endpoints
"""

import frappe
from frappe import _
import json
from idli_book.ai.llm_provider import LLMProvider
from idli_book.ai.action_executor import ActionExecutor

@frappe.whitelist()
def chat(message, session_id=None):
	"""
	Main chat endpoint
	Args:
		message: User's message
		session_id: Optional session ID for context
	Returns:
		{response: str, data: any, session_id: str}
	"""
	
	try:
		# Initialize LLM
		llm = LLMProvider()
		
		# Build conversation context
		messages = build_context(message, session_id)
		
		# Get available functions
		functions = ActionExecutor.get_available_functions()
		
		# Get LLM response
		llm_response = llm.chat(messages, functions)
		
		# If LLM wants to call a function (tool)
		if llm_response.get("function_call"):
			func_name = llm_response["function_call"]["name"]
			func_args = llm_response["function_call"]["arguments"]
			
			# Execute the function
			result = ActionExecutor.execute(func_name, func_args)
			
			# Format result for better display
			formatted_result = format_response(func_name, result)
			
			return {
				"response": formatted_result,
				"data": result.get("data"),
				"session_id": session_id or frappe.generate_hash(length=10)
			}
		else:
			# Direct response without function call
			return {
				"response": llm_response.get("content", ""),
				"data": None,
				"session_id": session_id or frappe.generate_hash(length=10)
			}
	
	except Exception as e:
		frappe.log_error(f"Chatbot Error: {str(e)}", "Chatbot Error")
		return {
			"response": _("I'm sorry, I encountered an error. Please try again."),
			"error": str(e),
			"session_id": session_id
		}

def format_response(func_name, result):
	"""Format function result into human-readable response"""
	if not result.get("success"):
		return result.get("message", "No results found")
	
	data = result.get("data", [])
	message = result.get("message", "")
	
	if func_name == "get_invoices":
		count = len(data) if isinstance(data, list) else 0
		total_outstanding = result.get("summary", {}).get("total_outstanding", 0)
		return f"Found {count} invoices. Total Outstanding: ₹{total_outstanding:,.2f}\n\n{message}"
	
	elif func_name == "get_customers":
		count = len(data) if isinstance(data, list) else 0
		return f"Found {count} customers.\n\n{message}"
	
	elif func_name == "get_payments":
		count = len(data) if isinstance(data, list) else 0
		total = result.get("summary", {}).get("total_amount", 0)
		return f"Found {count} payments. Total Amount: ₹{total:,.2f}\n\n{message}"
	
	elif func_name == "get_summary":
		return message
	
	return message

def build_context(message, session_id=None):
	"""Build conversation context"""
	
	system_prompt = """You are an AI assistant for Idli Book, an accounting software.

You help users with:
- Querying business data (customers, invoices, payments)
- Getting business insights and summaries
- Navigating the system

Be concise, professional, and helpful. When showing data, format it clearly.

Available functions:
- get_customers: List customers
- get_invoices: List sales invoices
- get_payments: List payment entries
- get_summary: Get business metrics

Current date: {today}
""".format(today=frappe.utils.today())
	
	messages = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": message}
	]
	
	# TODO: Add session-based context retrieval
	
	return messages

@frappe.whitelist()
def get_suggestions():
	"""Get quick action suggestions"""
	return {
		"suggestions": [
			"Show me unpaid invoices",
			"List all customers",
			"How much money am I owed?",
			"Show payments received today",
			"What's my total revenue this month?",
			"List top 5 customers",
		]
	}

@frappe.whitelist()
def clear_session(session_id):
	"""Clear chat session"""
	# TODO: Implement session clearing
	return {"success": True}
