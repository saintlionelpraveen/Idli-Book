frappe.ui.form.on('IB Purchase Order', {
    refresh: function (frm) {
        // Add Create Purchase Bill button after submit
        if (frm.doc.docstatus === 1 && frm.doc.status !== 'Billed') {
            frm.add_custom_button(__('Create Purchase Bill'), function () {
                frappe.call({
                    method: 'idli_book.idli_book.doctype.ib_purchase_order.ib_purchase_order.make_purchase_bill',
                    args: {
                        source_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route('Form', 'IB Purchase Bill', r.message.name);
                        }
                    }
                });
            }, __('Create'));
        }
    }
});

frappe.ui.form.on('IB Invoice Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'IB Item',
                    name: row.item_code
                },
                async: true,
                callback: function (r) {
                    if (r.message) {
                        // Auto-fill from item master
                        frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
                        frappe.model.set_value(cdt, cdn, 'description', r.message.purchase_description || r.message.sales_description);
                        frappe.model.set_value(cdt, cdn, 'uom', r.message.unit);
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.buying_price || 0);
                        frappe.model.set_value(cdt, cdn, 'tax_rate', r.message.tax_percentage || 0);
                    }
                }
            });
        }
    },
    quantity: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    rate: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },
    tax_rate: function (frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    }
});

function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = flt(row.quantity) * flt(row.rate);
    frm.refresh_field('items');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let subtotal = 0;
    let total_tax = 0;

    $.each(frm.doc.items || [], function (i, row) {
        let amount = flt(row.quantity) * flt(row.rate);
        subtotal += amount;

        if (row.tax_rate) {
            total_tax += amount * (row.tax_rate / 100);
        }
    });

    frm.set_value('subtotal', subtotal);
    frm.set_value('tax_amount', total_tax);

    let discount = flt(frm.doc.discount_amount) || 0;
    frm.set_value('grand_total', subtotal + total_tax - discount);
}
