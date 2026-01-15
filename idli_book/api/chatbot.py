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
			
			# --- Loopback Mechanism ---
			# Feed the result back to the LLM to get a natural language response
			
			# 0. Add the Model's turn (Critical for Gemini Strict Turn Order)
			# We insert a thought/action message to satisfy User -> Model -> User flow
			messages.append({
				"role": "assistant",
				"content": f"I will call the function '{func_name}' to retrieve the data."
			})

			# 1. Add the tool execution result to history
			# We use 'user' role to represent the system/environment providing data to the model
			messages.append({
				"role": "user", 
				"content": f"Function '{func_name}' executed successfully.\nResult: {json.dumps(result, default=str)}\n\nPlease summarize this for the user."
			})
			
			# 2. Get the final natural language response
			final_response = llm.chat(messages)
			
			return {
				"response": final_response.get("content", ""),
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
			"response": f"I'm sorry, I encountered an error: {str(e)}",
			"error": str(e),
			"session_id": session_id
		}

def build_context(message, session_id=None):
	"""Build conversation context"""
	
	# Get Dynamic Schema
	schema_info = get_doctype_schema()

	system_prompt = """You are an AI assistant for Idli Book, an accounting software.

You have access to the following Tables (DocTypes):
{schema}

You help users with:
- Querying business data
- getting details of records
- Getting business insights

Be concise, professional, and helpful. 
When asked to list or find records, use `get_table_list`.
When asked for specific details of a record, use `get_record_details`.
If unsure about which table to use, check the list above.

Current date: {today}
""".format(schema=schema_info, today=frappe.utils.today())
	
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

def get_doctype_schema():
	"""Fetch schema for all 'IB' DocTypes"""
	schema = []
	try:
		# Get all DocTypes starting with IB
		doctypes = frappe.get_all("DocType", filters={"name": ["like", "IB %"], "istable": 0}, pluck="name")
		
		for dt in doctypes:
			meta = frappe.get_meta(dt)
			# Get key fields (searchable or in list view)
			fields = [f.fieldname for f in meta.fields if f.in_list_view or f.bold]
			# Ensure name is there
			fields = ["name"] + fields[:5] # Limit to top 5 key fields to save tokens
			
			description = f"- {dt}: ({', '.join(fields)})"
			schema.append(description)
			
	except Exception as e:
		frappe.log_error(f"Schema Fetch Error: {str(e)}")
		return "Error fetching schema"
		
	return "\n".join(schema)

@frappe.whitelist()
def clear_session(session_id):
	"""Clear chat session"""
	# TODO: Implement session clearing
	return {"success": True}
