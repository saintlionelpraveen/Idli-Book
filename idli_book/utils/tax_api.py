import frappe
from idli_book.idli_book.utils.hsn_data import get_hsn_details, get_sac_details

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
