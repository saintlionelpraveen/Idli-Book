frappe.listview_settings['IB Sales Invoice'] = {
    formatters: {
        status(value) {
            const status_colors = {
                'Draft': 'gray',
                'Awaiting Payment': 'orange',
                'Partially Paid': 'yellow',
                'Paid': 'green',
                'Cancelled': 'red',
                'Overdue': 'darkred'
            };
            return `<span class="indicator-pill ${status_colors[value] || 'gray'}">${value}</span>`;
        }
    },

    get_indicator: function (doc) {
        const status_colors = {
            'Draft': ['Draft', 'gray', 'status,=,Draft'],
            'Awaiting Payment': ['Awaiting Payment', 'orange', 'status,=,Awaiting Payment'],
            'Partially Paid': ['Partially Paid', 'yellow', 'status,=,Partially Paid'],
            'Paid': ['Paid', 'green', 'status,=,Paid'],
            'Cancelled': ['Cancelled', 'red', 'status,=,Cancelled'],
            'Overdue': ['Overdue', 'darkred', 'status,=,Overdue']
        };
        return status_colors[doc.status] || ['Unknown', 'gray'];
    },

    onload: function (listview) {
        // Add custom columns for payment info
        listview.page.add_inner_button(__('Refresh'), function () {
            listview.refresh();
        });
    }
};
