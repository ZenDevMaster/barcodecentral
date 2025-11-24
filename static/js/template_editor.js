/**
 * Template Editor JavaScript
 * Handles template editing functionality with Ace Editor
 */

// Note: Most functionality is already embedded in new_template.html and edit_template.html
// This file provides additional utilities and can be extended

const TemplateEditor = {
    editor: null,
    autoSaveTimer: null,
    autoSaveInterval: 30000, // 30 seconds

    /**
     * Initialize the editor
     */
    init: function(elementId, options = {}) {
        const defaultOptions = {
            theme: 'ace/theme/monokai',
            mode: 'ace/mode/text',
            fontSize: '14px',
            showPrintMargin: false,
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: false
        };

        const mergedOptions = { ...defaultOptions, ...options };

        this.editor = ace.edit(elementId);
        this.editor.setTheme(mergedOptions.theme);
        this.editor.session.setMode(mergedOptions.mode);
        this.editor.setOptions({
            fontSize: mergedOptions.fontSize,
            showPrintMargin: mergedOptions.showPrintMargin,
            enableBasicAutocompletion: mergedOptions.enableBasicAutocompletion,
            enableLiveAutocompletion: mergedOptions.enableLiveAutocompletion
        });

        return this.editor;
    },

    /**
     * Get editor content
     */
    getContent: function() {
        return this.editor ? this.editor.getValue() : '';
    },

    /**
     * Set editor content
     */
    setContent: function(content) {
        if (this.editor) {
            this.editor.setValue(content, -1);
        }
    },

    /**
     * Extract variables from ZPL content
     */
    extractVariables: function(content) {
        const regex = /\{\{\s*(\w+)\s*\}\}/g;
        const matches = content.match(regex);
        
        if (!matches) return [];
        
        const variables = matches.map(m => m.replace(/\{\{\s*|\s*\}\}/g, ''));
        return [...new Set(variables)]; // Remove duplicates
    },

    /**
     * Validate ZPL syntax (basic validation)
     */
    validateZPL: function(content) {
        const errors = [];

        // Check for matching ^XA and ^XZ
        const xaCount = (content.match(/\^XA/g) || []).length;
        const xzCount = (content.match(/\^XZ/g) || []).length;

        if (xaCount === 0) {
            errors.push('Missing ^XA (start of label format)');
        }

        if (xzCount === 0) {
            errors.push('Missing ^XZ (end of label format)');
        }

        if (xaCount !== xzCount) {
            errors.push('Mismatched ^XA and ^XZ commands');
        }

        // Check for basic ZPL structure
        if (!content.includes('^FO')) {
            errors.push('No field origin (^FO) commands found');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Insert ZPL snippet at cursor
     */
    insertSnippet: function(snippet) {
        if (this.editor) {
            this.editor.insert(snippet);
            this.editor.focus();
        }
    },

    /**
     * Common ZPL snippets
     */
    snippets: {
        text: '^FO50,50^A0N,50,50^FDYour Text Here^FS',
        barcode: '^FO50,100^BY3^BCN,100,Y,N,N^FD123456789^FS',
        qrcode: '^FO50,200^BQN,2,10^FDQA,Your Data Here^FS',
        line: '^FO50,300^GB400,2,2^FS',
        box: '^FO50,350^GB400,100,2^FS',
        variable: '{{variable_name}}'
    },

    /**
     * Format ZPL code (basic formatting)
     */
    formatCode: function() {
        if (!this.editor) return;

        let content = this.editor.getValue();
        
        // Add newlines after major commands
        content = content.replace(/(\^XA)/g, '$1\n');
        content = content.replace(/(\^XZ)/g, '\n$1');
        content = content.replace(/(\^FS)/g, '$1\n');
        
        // Remove excessive blank lines
        content = content.replace(/\n{3,}/g, '\n\n');
        
        this.editor.setValue(content, -1);
        showToast('Code formatted', 'success');
    },

    /**
     * Enable auto-save
     */
    enableAutoSave: function(saveCallback) {
        this.disableAutoSave(); // Clear any existing timer

        this.autoSaveTimer = setInterval(() => {
            if (this.editor && saveCallback) {
                const content = this.getContent();
                saveCallback(content);
                console.log('Auto-saved at', new Date().toLocaleTimeString());
            }
        }, this.autoSaveInterval);
    },

    /**
     * Disable auto-save
     */
    disableAutoSave: function() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    },

    /**
     * Search and replace in editor
     */
    searchReplace: function(searchTerm, replaceTerm, replaceAll = false) {
        if (!this.editor) return;

        const options = {
            needle: searchTerm,
            backwards: false,
            wrap: true,
            caseSensitive: false,
            wholeWord: false,
            regExp: false
        };

        if (replaceAll) {
            this.editor.replaceAll(replaceTerm, options);
            showToast('All occurrences replaced', 'success');
        } else {
            this.editor.find(searchTerm, options);
            this.editor.replace(replaceTerm);
            showToast('Replaced', 'success');
        }
    },

    /**
     * Undo last change
     */
    undo: function() {
        if (this.editor) {
            this.editor.undo();
        }
    },

    /**
     * Redo last undone change
     */
    redo: function() {
        if (this.editor) {
            this.editor.redo();
        }
    },

    /**
     * Get cursor position
     */
    getCursorPosition: function() {
        if (this.editor) {
            return this.editor.getCursorPosition();
        }
        return null;
    },

    /**
     * Set cursor position
     */
    setCursorPosition: function(row, column) {
        if (this.editor) {
            this.editor.moveCursorTo(row, column);
            this.editor.focus();
        }
    },

    /**
     * Get selected text
     */
    getSelectedText: function() {
        if (this.editor) {
            return this.editor.getSelectedText();
        }
        return '';
    },

    /**
     * Clear editor content
     */
    clear: function() {
        if (this.editor) {
            this.editor.setValue('', -1);
        }
    },

    /**
     * Set read-only mode
     */
    setReadOnly: function(readOnly) {
        if (this.editor) {
            this.editor.setReadOnly(readOnly);
        }
    },

    /**
     * Destroy editor instance
     */
    destroy: function() {
        this.disableAutoSave();
        if (this.editor) {
            this.editor.destroy();
            this.editor = null;
        }
    }
};

// Make TemplateEditor available globally
window.TemplateEditor = TemplateEditor;