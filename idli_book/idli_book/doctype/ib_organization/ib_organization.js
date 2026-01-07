// Copyright (c) 2025, Idli Book and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB Organization', {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button('⚠ Reset Chart of Accounts', function () {
                frappe.confirm('Are you sure you want to DELETE ALL ACCOUNTS?', () => {
                    frappe.call({
                        method: 'idli_book.idli_book.doctype.ib_organization.ib_organization.reset_chart_of_accounts',
                        callback: function (r) {
                            frappe.msgprint("All accounts deleted.");
                            frm.reload_doc();
                        }
                    });
                });
            }, 'Actions');
        }
    }
});
