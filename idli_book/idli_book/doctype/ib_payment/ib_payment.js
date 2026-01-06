frappe.ui.form.on('IB Payment', {
    setup: function (frm) {
        // Capture context securely
        if (frappe.route_options && frappe.route_options.linked_invoice) {
            frm._linked_invoice = frappe.route_options.linked_invoice;
        }
    },
    refresh: function (frm) {
        // Trigger robust DB fix
        frappe.call({
            method: 'idli_book.idli_book.doctype.ib_payment.ib_payment.fix_db_schema',
            callback: function (r) { console.log("Schema Fix Attempted"); }
        });

        if (frm.doc.mode_of_payment) {
            frm.trigger('mode_of_payment');
        }

        // Auto-trigger party logic if populated and table empty
        if (frm.doc.party && (!frm.doc.references || frm.doc.references.length === 0)) {
            frm.trigger('party');
        }
    },
    mode_of_payment: function (frm) {
        // Hide both account fields - backend auto-fills based on customer/organization
        frm.set_df_property('paid_to_account', 'hidden', 1);
        frm.set_df_property('paid_from_account', 'hidden', 1);
        frm.set_df_property('paid_to_account', 'reqd', 0);
        frm.set_df_property('paid_from_account', 'reqd', 0);
    },
    party: function (frm) {
        if (frm.doc.party && frm.doc.party_type == "IB Customer") {
            // Check for specific linked invoice context
            if (frm._linked_invoice) {
                var linked_invoice = frm._linked_invoice;
                // Don't clear it, keep context for this session

                frappe.call({
                    method: 'frappe.client.get',
                    args: { doctype: "IB Sales Invoice", name: linked_invoice },
                    callback: function (r) {
                        if (r.message && r.message.name) {
                            var inv = r.message;
                            frm.clear_table('references');
                            var row = frm.add_child('references');
                            row.reference_doctype = "IB Sales Invoice";
                            row.reference_name = inv.name;
                            row.total_amount = inv.grand_total;
                            row.outstanding_amount = inv.outstanding_amount;
                            row.allocated_amount = inv.outstanding_amount; // Default to full outstanding
                            frm.refresh_field('references');
                            frm.events.calculate_unallocated(frm);
                        }
                    }
                });
            } else {
                // Bulk Fetch Logic only if NO Context
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'IB Sales Invoice',
                        filters: {
                            customer: frm.doc.party,
                            docstatus: 1,
                            status: ['!=', 'Paid']
                        },
                        fields: ['name', 'grand_total', 'outstanding_amount']
                    },
                    callback: function (r) {
                        if (r.message) {
                            frm.clear_table('references');
                            $.each(r.message, function (i, d) {
                                var row = frm.add_child('references');
                                row.reference_doctype = "IB Sales Invoice";
                                row.reference_name = d.name;
                                row.total_amount = d.grand_total;
                                row.outstanding_amount = d.outstanding_amount;
                                row.allocated_amount = 0;
                            });
                            frm.refresh_field('references');
                            frm.events.calculate_unallocated(frm);
                        }
                    }
                });
            }
        }
    },
    amount: function (frm) {
        // Auto-update allocation if there is a single reference
        if (frm.doc.references && frm.doc.references.length === 1) {
            var row = frm.doc.references[0];
            var new_amount = flt(frm.doc.amount);

            // Smartly capping allocation at outstanding amount
            var alloc = new_amount;
            if (alloc > row.outstanding_amount) {
                alloc = row.outstanding_amount;
            }

            // Update the allocated amount
            frappe.model.set_value(row.doctype, row.name, "allocated_amount", alloc);

            // Force refresh to ensure UI updates
            setTimeout(() => {
                frm.refresh_field('references');
                frm.events.calculate_unallocated(frm);
            }, 100);
        } else {
            frm.events.calculate_unallocated(frm);
        }
    },
    calculate_unallocated: function (frm) {
        var total_allocated = 0;
        $.each(frm.doc.references || [], function (i, row) {
            total_allocated += flt(row.allocated_amount);
        });
        frm.set_value("unallocated_amount", frm.doc.amount - total_allocated);
    }
});

frappe.ui.form.on('IB Payment Reference', {
    allocated_amount: function (frm, cdt, cdn) {
        frm.events.calculate_unallocated(frm);
    }
});
