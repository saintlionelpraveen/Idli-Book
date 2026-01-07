import frappe
import requests
from frappe.utils import flt
from .hsn_data import get_hsn_details, get_sac_details

class TaxAPI:
	
	@staticmethod
	@frappe.whitelist()
	def get_code_details(code, type="HSN"):
		"""
		Smart API:
		1. Check DB (IB HSN Code / IB SAC Code)
		2. If missing, look in hsn_data.py
		3. If found in data, CREATE new record in DB
		4. Return details
		"""
		if not code:
			return None
			
		doctype = "IB HSN Code" if type == "HSN" else "IB SAC Code"
		
		# Field name check: HSN Doctype uses 'hsn_code', SAC Doctype uses 'sac_code'
		field = "hsn_code" if type == "HSN" else "sac_code"
		
		# 1. Check Database
		if frappe.db.exists(doctype, code):
			doc = frappe.get_doc(doctype, code)
			return {
				"valid": True,
				"description": doc.description,
				"tax_rate": doc.tax_rate,
				"source": "database"
			}
			
		# 2. Not in DB? Check Static Data
		data = None
		if type == "HSN":
			data = get_hsn_details(str(code))
		elif type == "SAC":
			data = get_sac_details(str(code))
			
		if data:
			# 3. Auto-Create in Database
			try:
				new_doc = frappe.get_doc({
					"doctype": doctype,
					field: code,
					"description": data['description'],
					"tax_rate": data['tax_rate']
				})
				new_doc.insert(ignore_permissions=True)
				frappe.db.commit()
				
				return {
					"valid": True,
					"description": data['description'],
					"tax_rate": data['tax_rate'],
					"source": "auto-created"
				}
			except Exception as e:
				frappe.log_error(f"Failed to auto-create {type} code {code}: {str(e)}")
				return {
					"valid": True,
					"description": data['description'],
					"tax_rate": data['tax_rate'],
					"source": "static-fallback"
				}
		
		# 4. Not found anywhere
		return {
			"valid": False,
			"message": f"{type} Code {code} not found in system or global database."
		}

	@staticmethod
	@frappe.whitelist()
	def get_state_from_pincode(pincode):
		"""Get state from pincode using India Post API"""
		if not pincode or len(str(pincode)) != 6:
			return None
		
		try:
			url = f"https://api.postalpincode.in/pincode/{pincode}"
			response = requests.get(url, timeout=5)
			data = response.json()
			
			if data and data[0].get("Status") == "Success":
				state_name = data[0]["PostOffice"][0]["State"]
				# Find matching state in our database
				state = frappe.db.get_value("IB State", {"state_name": state_name}) # Updated to IB State
				return state
		except Exception as e:
			frappe.log_error(f"Pincode API Error: {str(e)}")
		
		return None

	@staticmethod
	@frappe.whitelist()
	def validate_gstin(gstin):
		"""
		Validate GSTIN format
		"""
		if not gstin or len(gstin) != 15:
			return {"valid": False, "message": "GSTIN must be 15 characters"}
		
		# Extract state code
		state_code = gstin[:2]
		
		# Check if state code exists
		state = frappe.db.get_value("IB State", {"state_code": state_code}) # Updated to IB State
		
		if not state:
			return {"valid": False, "message": f"Invalid state code: {state_code}"}
		
		return {
			"valid": True,
			"state": state,
			"state_code": state_code
		}
