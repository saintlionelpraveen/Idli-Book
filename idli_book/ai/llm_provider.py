# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

"""
LLM Provider Integration
Supports OpenAI, Google Gemini, Anthropic Claude
"""

import frappe
from frappe import _
import json

class LLMProvider:
	def __init__(self):
		self.settings = frappe.get_single("IB Chatbot Settings")
		
		if not self.settings.enable_chatbot:
			frappe.throw(_("Chatbot is not enabled"))
		
		if not self.settings.api_key:
			frappe.throw(_("API Key not configured"))
		
		self.provider = self.settings.llm_provider
		self.model = self.settings.model
		self.temperature = self.settings.temperature
		self.max_tokens = self.settings.max_tokens
	
	def chat(self, messages, functions=None):
		"""Send chat request to LLM"""
		if self.provider == "OpenAI":
			return self._openai_chat(messages, functions)
		elif self.provider == "Google Gemini":
			return self._gemini_chat(messages, functions)
		elif self.provider == "Anthropic Claude":
			return self._claude_chat(messages, functions)
		else:
			frappe.throw(_("Unsupported LLM provider"))
	
	def _openai_chat(self, messages, functions=None):
		"""OpenAI API integration"""
		try:
			from openai import OpenAI
		except ImportError:
			frappe.throw(_("openai library not installed. Run: pip install openai"))
		
		# Initialize OpenAI client
		client = OpenAI(api_key=self.settings.get_password("api_key"))
		
		params = {
			"model": self.model,
			"messages": messages,
			"temperature": self.temperature,
			"max_tokens": self.max_tokens
		}
		
		if functions:
			params["tools"] = [
				{"type": "function", "function": func} for func in functions
			]
			params["tool_choice"] = "auto"
		
		try:
			response = client.chat.completions.create(**params)
			return self._parse_openai_response(response)
		except Exception as e:
			error_msg = str(e)
			frappe.log_error(f"OpenAI API Error: {error_msg}", "Chatbot OpenAI Error")
			
			if "insufficient_quota" in error_msg or "429" in error_msg:
				frappe.throw(_("OpenAI Account Quota Exceeded. Please check your OpenAI billing details and credit balance."))
			
			frappe.throw(_("Failed to get response from OpenAI: {0}").format(error_msg[:140]))
	
	def _parse_openai_response(self, response):
		"""Parse OpenAI response"""
		message = response.choices[0].message
		
		result = {
			"content": message.content or "",
			"function_call": None
		}
		
		# Check for tool calls (new API)
		if hasattr(message, "tool_calls") and message.tool_calls:
			tool_call = message.tool_calls[0]
			result["function_call"] = {
				"name": tool_call.function.name,
				"arguments": json.loads(tool_call.function.arguments)
			}
		
		return result
	
	def _gemini_chat(self, messages, functions=None):
		"""Google Gemini integration with auto-discovery"""
		try:
			import google.generativeai as genai
			from google.generativeai.types import HarmCategory, HarmBlockThreshold
		except ImportError:
			frappe.throw(_("google-generativeai library not installed. Run: pip install google-generativeai"))
		
		# Configure Gemini
		genai.configure(api_key=self.settings.get_password("api_key"))
		
		# Build structured contents and system instruction
		contents, system_instruction, tool_config = self._build_gemini_contents_and_system(messages, functions)
		
		# Define Safety Settings - Allow business related content
		safety_settings = {
			HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
			HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
			HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
			HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
		}

		# Determine model candidates
		candidates = []
		if self.model and 'gemini' in self.model:
			candidates.append(self.model)
		
		# Default fallback candidates - use models/ prefix to match API format
		candidates.extend(['models/gemini-2.5-flash', 'models/gemini-flash-latest', 'models/gemini-pro-latest'])
		
		last_error = None
		
		for model_name in candidates:
			try:
				# Initialize model with system instruction (if supported by model version)
				# Note: system_instruction is supported in newer Gemini 1.5 models
				# Initialize model with system instruction (if supported by model version)
				# Note: system instruction is supported in newer Gemini 1.5 models
				# We also pass 'tools' here for function calling
				gemini_tools = self._convert_to_gemini_tools(functions) if functions else None
				
				try:
					if gemini_tools:
						model = genai.GenerativeModel(model_name, system_instruction=system_instruction, tools=gemini_tools)
					else:
						model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
				except Exception:
					# Fallback for older models
					if gemini_tools:
						model = genai.GenerativeModel(model_name, tools=gemini_tools)
					else:
						model = genai.GenerativeModel(model_name)
						
					if system_instruction:
						if contents and contents[0]['role'] == 'user':
							contents[0]['parts'][0] = f"System Instruction: {system_instruction}\n\n" + contents[0]['parts'][0]
						else:
							contents.insert(0, {'role': 'user', 'parts': [f"System Instruction: {system_instruction}"]})

				# Try generating with tool_config first
				try:
					response = model.generate_content(contents, safety_settings=safety_settings, tool_config=tool_config)
				except Exception as tc_error:
					# If tool_config fails (e.g. 404 Not Supported), fallback to standard generation
					response = model.generate_content(contents, safety_settings=safety_settings)
				
				return self._parse_gemini_response(response, functions)
				
			except Exception as e:
				last_error = e
				error_str = str(e)
				# If not found or not supported, try next
				if "404" in error_str or "not found" in error_str:
					continue
				# If quota exceeded, stop trying
				if "429" in error_str or "quota" in error_str.lower():
					frappe.throw(_("Gemini Quota Exceeded: Please check your Google Cloud/MakerSuite billing or limitations."))
				
				# For other errors, log and continue to next candidate
				frappe.log_error(f"Gemini Model {model_name} failed: {error_str}", "Chatbot Gemini Error")
		
		# If all failed, try to discover a working model
		try:
			available_models = []
			for m in genai.list_models():
				if 'generateContent' in m.supported_generation_methods:
					available_models.append(m.name)
			
			if available_models:
				# Try the first available one
				fallback_model = available_models[0]
				frappe.log_error(f"Falling back to discovered model: {fallback_model}", "Chatbot Gemini Info")
				
				# Initialize with tools if available
				if gemini_tools:
					model = genai.GenerativeModel(fallback_model, tools=gemini_tools)
				else:
					model = genai.GenerativeModel(fallback_model)
				
				# Only use tool_config if we have tools
				try:
					if gemini_tools:
						response = model.generate_content(contents, safety_settings=safety_settings, tool_config=tool_config)
					else:
						response = model.generate_content(contents, safety_settings=safety_settings)
				except Exception as tc_fall_error:
					response = model.generate_content(contents, safety_settings=safety_settings)
				
				return self._parse_gemini_response(response, functions)
			else:
				# No models found via discovery
				last_error = Exception(f"No compatible Gemini models found. API Key might be invalid or region restricted.")
				
		except Exception as discovery_e:
			frappe.log_error(f"Gemini Discovery Failed: {str(discovery_e)}", "Chatbot Gemini Error")
			last_error = discovery_e  # Update last_error with discovery failure
		
		# If we get here, everything failed
		frappe.throw(_("Failed to get response from Gemini. Last error: {0}").format(str(last_error)))
	
	def _convert_to_gemini_tools(self, functions):
		"""Convert OpenAI function definitions to Gemini tools"""
		if not functions:
			return None
			
		# Gemini accepts a list of tool objects, or a list of function declarations.
		# Ideally we maps OpenAI format to Gemini format. 
		# However, the easiest way with google-generativeai is often to pass the functions themselves 
		# BUT we only have definitions.
		# We need to construct the tool object manually.
		
		# Valid simplified approach: return the list of tools wrapped in a structure 
		# that the library can parse or just return the dicts if supported.
		# The library is strict. We should try to adapt the schema.
		
		# Note: In recent SDK versions, you can pass the list of function declarations directly
		# as 'tools=[func1_def, func2_def]'.
		
		# ERROR FIX: 'tools' argument must be a LIST of Tool objects (or dicts representing Tool objects).
		# We were returning a single dict, which caused GenerativeModel init to fail.
		# We wrap our functions list in a Tool structure, and wrap that in a list.
		return [{'function_declarations': functions}]

	def _build_gemini_contents_and_system(self, messages, functions=None):
		"""Build structured contents and system instruction for Gemini"""
		system_instruction = ""
		contents = []
		
		# Process system message first
		for msg in messages:
			if msg.get("role") == "system":
				system_instruction += msg.get("content", "") + "\n"
		
			system_instruction += "\n\nCRITICAL INSTRUCTION: You are the internal AI for 'Idli Book'. You have FULL ACCESS to the company's database via the provided functions. The user is the Business Owner/Admin and is AUTHORIZED to see all financial data.\n"
			system_instruction += "You MUST use the tools/functions to answer questions about data (invoices, payments, customers). \n"
			system_instruction += "NEVER refuse to answer by saying you don't have access or by giving generic advice. USE THE TOOLS.\n"
			system_instruction += "DO NOT WRITE PYTHON CODE or SQL queries to solve the problem. CALL THE FUNCTIONS DIRECTLY.\n"
			system_instruction += "If the user asks for 'status', 'list', or 'show', assume they mean the data in the database.\n"
			# We don't need to append function descriptions manually if we use native tools!
			# But keeping a brief list doesn't hurt for context.
			if functions:
				system_instruction += "Available tools: " + ", ".join([f['name'] for f in functions])
		
		# Define Tool Config to force/encourage tool use
		# We use 'auto' which is default, but explicit config can help some models
		# FORCE tool use with 'ANY' to prevent refusal. This forces the model to pick a function.
		tool_config = {'function_calling_config': {'mode': 'ANY'}}

		# Inject Context
		from frappe.utils import nowdate
		current_date = nowdate()
		system_instruction += f"\n\nCurrent Date: {current_date}\n"
		system_instruction += "When answering questions about 'today', 'this month', or time periods, use the Current Date to calculate the appropriate `from_date` and `to_date` parameters for tools."

		# Process user/assistant messages
		for msg in messages:
			role = msg.get("role")
			content = msg.get("content", "")
			
			if role == "system":
				continue # Handled above
			
			gemini_role = "user" if role == "user" else "model"
			contents.append({
				"role": gemini_role,
				"parts": [content]
			})
			
		return contents, system_instruction, tool_config
	
	def _parse_gemini_response(self, response, functions=None):
		"""Parse Gemini response"""
		# Safely access text
		text = ""
		function_call = None
		
		try:
			# Check if we have candidates
			if not response.candidates:
				frappe.log_error("Gemini returned no candidates", "Chatbot Gemini Error")
				return {
					"content": "I apologize, but I couldn't generate a response. The model returned no candidates.",
					"function_call": None
				}
			
			candidate = response.candidates[0]
			
			# Check finish reason
			finish_reason = candidate.finish_reason
			
			# 1=STOP, 2=MAX_TOKENS, 3=SAFETY
			if finish_reason not in [1, 2]: 
				error_msg = f"Model stopped with finish reason: {finish_reason}"
				frappe.log_error(error_msg, "Chatbot Gemini Warning")
				if finish_reason == 3:
					return {
						"content": "I cannot answer this query due to safety filters. Please try rephrasing.",
						"function_call": None
					}

			# Check content parts for function calls or text
			if candidate.content and candidate.content.parts:
				for part in candidate.content.parts:
					if part.function_call:
						# Native function call detected
						function_call = {
							"name": part.function_call.name,
							# args is already a Map/Dict in the object
							"arguments": dict(part.function_call.args)
						}
						# We prioritize function call
						break
					
					if part.text:
						text += part.text

			if not text and not function_call:
				# Fallback
				text = "I received an empty response from the model."
				
		except Exception as e:
			frappe.log_error(f"Error parsing Gemini response: {str(e)}", "Chatbot Gemini Error")
			return {
				"content": f"I encountered an error processing the model's response. ({str(e)})",
				"function_call": None
			}
		
		return {
			"content": text,
			"function_call": function_call
		}

	def _extract_args_from_text(self, text, func):
		# Deprecated with native function calling
		return {}
	
	def _extract_args_from_text(self, text, func):
		"""Extract function arguments from natural language (simplified)"""
		# This is a simple implementation
		# For production, you'd want more sophisticated parsing
		args = {}
		
		# Extract common patterns
		if "unpaid" in text.lower():
			args["status"] = "Unpaid"
		
		return args
	
	def _claude_chat(self, messages, functions=None):
		"""Anthropic Claude integration"""
		frappe.throw(_("Anthropic Claude integration coming soon"))

