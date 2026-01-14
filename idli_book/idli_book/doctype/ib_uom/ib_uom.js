// Copyright (c) 2026, Praveen and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB UOM', {
    refresh: function (frm) {
        // Add help text
        if (frm.doc.__islocal) {
            frm.set_intro(__('Create a new unit of measurement'));
        }
    }
});
