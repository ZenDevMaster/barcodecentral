/**
 * Print Form JavaScript
 * Handles print form functionality, dynamic fields, and live preview
 */

// Note: Most functionality is already embedded in print_form.html
// This file provides additional utilities and can be extended

// Additional helper functions for print form
const PrintForm = {
    /**
     * Validate print form data
     */
    validate: function(formData) {
        const errors = [];

        if (!formData.template_name) {
            errors.push('Please select a template');
        }

        if (!formData.printer_name) {
            errors.push('Please select a printer');
        }

        if (!formData.quantity || formData.quantity < 1 || formData.quantity > 100) {
            errors.push('Quantity must be between 1 and 100');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Get form data as object
     */
    getFormData: function() {
        const formData = {
            template_name: $('#templateSelect').val(),
            printer_name: $('#printerSelect').val(),
            quantity: parseInt($('#quantity').val()),
            variables: {}
        };

        // Collect variable values
        $('.variable-input').each(function() {
            const varName = $(this).data('variable');
            formData.variables[varName] = $(this).val();
        });

        return formData;
    },

    /**
     * Reset form to initial state
     */
    reset: function() {
        $('#printForm')[0].reset();
        $('#variablesCard').hide();
        $('#variableFields').empty();
        $('#previewContent').empty();
        $('#previewPlaceholder').show();
        $('#previewError').hide();
        $('#printerWarning').hide();
    },

    /**
     * Populate form with data (for reprinting)
     */
    populate: function(data) {
        if (data.template_name) {
            $('#templateSelect').val(data.template_name).trigger('change');
        }

        if (data.printer_name) {
            $('#printerSelect').val(data.printer_name);
        }

        if (data.quantity) {
            $('#quantity').val(data.quantity);
        }

        // Wait for variable fields to be generated, then populate
        setTimeout(() => {
            if (data.variables) {
                Object.keys(data.variables).forEach(key => {
                    $(`#var_${key}`).val(data.variables[key]);
                });
            }
        }, 500);
    },

    /**
     * Export print job data
     */
    export: function() {
        const formData = this.getFormData();
        const dataStr = JSON.stringify(formData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `print_job_${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showToast('Print job data exported', 'success');
    },

    /**
     * Import print job data
     */
    import: function(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.populate(data);
                showToast('Print job data imported', 'success');
            } catch (error) {
                showToast('Failed to import: Invalid file format', 'danger');
            }
        };
        reader.readAsText(file);
    }
};

// Make PrintForm available globally
window.PrintForm = PrintForm;