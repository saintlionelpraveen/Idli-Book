# -*- coding: utf-8 -*-
# Copyright (c) 2025, Idli Book and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class IBItem(Document):
	@property
	def stock_status(self):
		"""Returns stock status for list view indicator"""
		if not self.track_inventory:
			return "Not Tracked"
		
		stock_qty = self.stock_quantity or 0
		reorder_level = self.reorder_level or 0
		
		if reorder_level > 0 and stock_qty < reorder_level:
			return "Low Stock"
		elif stock_qty > 0:
			return "Stock Good"
		else:
			return "Out of Stock"

# --- PROPER HSN/SAC DATA WITH OFFICIAL DESCRIPTIONS ---
HSN_DATA = {
    # Electronics & Computers
    '8471': {'description': 'Automatic data processing machines and units thereof; Magnetic or optical readers, machines for transcribing data on to data media in coded form and machines for processing such data, not elsewhere specified or included', 'tax_rate': 18, 'cat': 'Electronics'},
    '847130': {'description': 'Portable automatic data processing machines, weighing not more than 10 kg, consisting of at least a central processing unit, a keyboard and a display', 'tax_rate': 18, 'cat': 'Electronics'},
    '847160': {'description': 'Input or output units, whether or not containing storage units in the same housing', 'tax_rate': 18, 'cat': 'Electronics'},
    '84716040': {'description': 'Keyboard', 'tax_rate': 18, 'cat': 'Electronics'},
    '84716060': {'description': 'Mouse', 'tax_rate': 18, 'cat': 'Electronics'},
    '8517': {'description': 'Telephone sets, including telephones for cellular networks or for other wireless networks; other apparatus for the transmission or reception of voice, images or other data', 'tax_rate': 18, 'cat': 'Electronics'},
    
    # Food Products
    '0201': {'description': 'Meat of bovine animals, fresh or chilled', 'tax_rate': 0, 'cat': 'Food'},
    '1006': {'description': 'Rice', 'tax_rate': 5, 'cat': 'Food'},
    '2106': {'description': 'Food preparations not elsewhere specified or included', 'tax_rate': 18, 'cat': 'Food'},
    
    # Vehicles
    '8703': {'description': 'Motor cars and other motor vehicles principally designed for the transport of persons (other than those of heading 8702), including station wagons and racing cars', 'tax_rate': 28, 'cat': 'Vehicles'},
}

SAC_DATA = {
    # IT Services
    '998313': {'description': 'Information technology (IT) consulting and support services', 'tax_rate': 18, 'cat': 'IT Services'},
    '998314': {'description': 'Information technology (IT) design and development services', 'tax_rate': 18, 'cat': 'IT Services'},
    
    # Professional
    '998211': {'description': 'Legal services', 'tax_rate': 18, 'cat': 'Professional'},
    '998222': {'description': 'Accounting, auditing and bookkeeping services', 'tax_rate': 18, 'cat': 'Professional'},
    
    # Education
    '999293': {'description': 'Commercial training and coaching services', 'tax_rate': 18, 'cat': 'Education'},
}
# ---------------------------------------------------------

@frappe.whitelist()
def get_code_details_safe(code, type="HSN"):
	"""
	Robust API inside IB Item controller.
	"""
	if not code:
		return None
		
	doctype = "IB HSN Code" if type == "HSN" else "IB SAC Code"
	field = "hsn_code" if type == "HSN" else "sac_code"
	
	# 1. Check Database (The new separate doctypes)
	if frappe.db.exists(doctype, code):
		doc = frappe.get_doc(doctype, code)
		return {
			"valid": True,
			"description": doc.description,
			"tax_rate": doc.tax_rate,
			"source": "database"
		}
		
	# 2. Check Static Data
	data = None
	str_code = str(code)
	
	if type == "HSN":
		# Exact Match
		if str_code in HSN_DATA: 
			data = HSN_DATA[str_code]
		# 6-Digit Match
		elif len(str_code) >= 6 and str_code[:6] in HSN_DATA:
			data = HSN_DATA[str_code[:6]]
		# 4-Digit Match
		elif len(str_code) >= 4 and str_code[:4] in HSN_DATA:
			data = HSN_DATA[str_code[:4]]
			
	else:
		if str_code in SAC_DATA: 
			data = SAC_DATA[str_code]
		elif len(str_code) >= 6 and str_code[:6] in SAC_DATA:
			data = SAC_DATA[str_code[:6]]
		elif len(str_code) >= 4 and str_code[:4] in SAC_DATA:
			data = SAC_DATA[str_code[:4]]
			
	if data:
		# 3. Auto-Create in Database with CATEGORY
		try:
			# Prepare Doc Dict
			new_doc_data = {
				"doctype": doctype,
				field: code,
				"description": data['description'],
				"tax_rate": data['tax_rate']
			}
			
			# Add Category based on Type
			if type == "HSN":
				new_doc_data["item_category"] = "Goods" 
			else:
				new_doc_data["service_category"] = "Services"
				
			new_doc = frappe.get_doc(new_doc_data)
			new_doc.insert(ignore_permissions=True)
			
			return {
				"valid": True,
				"description": data['description'],
				"tax_rate": data['tax_rate'],
				"source": "auto-created"
			}
		except Exception as e:
			frappe.log_error(f"Auto-create failed: {str(e)}")
			return {
				"valid": True,
				"description": data['description'],
				"tax_rate": data['tax_rate'],
				"source": "static-fallback"
			}
	
	return {"valid": False, "message": "Code not found"}
