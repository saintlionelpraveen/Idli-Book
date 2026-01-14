# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe

no_cache = 1

def get_context(context):
	context.no_breadcrumbs = True
	context.title = "Idli Book Assistant"
