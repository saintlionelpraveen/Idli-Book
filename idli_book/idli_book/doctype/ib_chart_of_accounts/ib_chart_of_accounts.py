# Copyright (c) 2025, You and contributors
# For license information, please see license.txt

from frappe.utils.nestedset import NestedSet

class IBChartofAccounts(NestedSet):
	nsm_parent_field = 'parent_account'
