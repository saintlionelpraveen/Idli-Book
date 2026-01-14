// Copyright (c) 2026, Praveen and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB Country', {
    refresh: function (frm) {
        if (frm.doc.__islocal) {
            frm.set_intro(__('Create a new country'));
        }
    }
});
