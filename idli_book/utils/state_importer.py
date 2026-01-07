"""
Import Indian States and Union Territories
"""
import frappe

def import_indian_states():
	"""Import all Indian states and UTs"""
	
	states_data = [
		# States
		{"state_name": "Andhra Pradesh", "state_code": "37", "is_union_territory": 0},
		{"state_name": "Arunachal Pradesh", "state_code": "12", "is_union_territory": 0},
		{"state_name": "Assam", "state_code": "18", "is_union_territory": 0},
		{"state_name": "Bihar", "state_code": "10", "is_union_territory": 0},
		{"state_name": "Chhattisgarh", "state_code": "22", "is_union_territory": 0},
		{"state_name": "Goa", "state_code": "30", "is_union_territory": 0},
		{"state_name": "Gujarat", "state_code": "24", "is_union_territory": 0},
		{"state_name": "Haryana", "state_code": "06", "is_union_territory": 0},
		{"state_name": "Himachal Pradesh", "state_code": "02", "is_union_territory": 0},
		{"state_name": "Jharkhand", "state_code": "20", "is_union_territory": 0},
		{"state_name": "Karnataka", "state_code": "29", "is_union_territory": 0},
		{"state_name": "Kerala", "state_code": "32", "is_union_territory": 0},
		{"state_name": "Madhya Pradesh", "state_code": "23", "is_union_territory": 0},
		{"state_name": "Maharashtra", "state_code": "27", "is_union_territory": 0},
		{"state_name": "Manipur", "state_code": "14", "is_union_territory": 0},
		{"state_name": "Meghalaya", "state_code": "17", "is_union_territory": 0},
		{"state_name": "Mizoram", "state_code": "15", "is_union_territory": 0},
		{"state_name": "Nagaland", "state_code": "13", "is_union_territory": 0},
		{"state_name": "Odisha", "state_code": "21", "is_union_territory": 0},
		{"state_name": "Punjab", "state_code": "03", "is_union_territory": 0},
		{"state_name": "Rajasthan", "state_code": "08", "is_union_territory": 0},
		{"state_name": "Sikkim", "state_code": "11", "is_union_territory": 0},
		{"state_name": "Tamil Nadu", "state_code": "33", "is_union_territory": 0},
		{"state_name": "Telangana", "state_code": "36", "is_union_territory": 0},
		{"state_name": "Tripura", "state_code": "16", "is_union_territory": 0},
		{"state_name": "Uttar Pradesh", "state_code": "09", "is_union_territory": 0},
		{"state_name": "Uttarakhand", "state_code": "05", "is_union_territory": 0},
		{"state_name": "West Bengal", "state_code": "19", "is_union_territory": 0},
		
		# Union Territories
		{"state_name": "Andaman and Nicobar Islands", "state_code": "35", "is_union_territory": 1},
		{"state_name": "Chandigarh", "state_code": "04", "is_union_territory": 1},
		{"state_name": "Dadra and Nagar Haveli and Daman and Diu", "state_code": "26", "is_union_territory": 1},
		{"state_name": "Delhi", "state_code": "07", "is_union_territory": 1},
		{"state_name": "Jammu and Kashmir", "state_code": "01", "is_union_territory": 1},
		{"state_name": "Ladakh", "state_code": "38", "is_union_territory": 1},
		{"state_name": "Lakshadweep", "state_code": "31", "is_union_territory": 1},
		{"state_name": "Puducherry", "state_code": "34", "is_union_territory": 1}
	]
	
	created_count = 0
	
	for state_data in states_data:
		# Check if already exists
		if not frappe.db.exists("State", state_data["state_name"]):
			state = frappe.get_doc({
				"doctype": "State",
				**state_data
			})
			state.insert(ignore_permissions=True)
			created_count += 1
	
	frappe.db.commit()
	
	return {
		"success": True,
		"message": f"Imported {created_count} states/UTs",
		"total": len(states_data)
	}

@frappe.whitelist()
def run_state_import():
	"""API endpoint to import states"""
	return import_indian_states()
