// templates.js
export const Templates = {
    /**
     * Generates HTML for the Filter Toolbar
     */
    filterToolbar() {
        return `
            <div class="config-filter-group">
                <input type="text" id="config-modal-search" class="config-filter-input" placeholder="Search rule names..." autocomplete="off" />
            </div>
            <div class="config-filter-group">
                <label for="config-modal-filter-status">Status:</label>
                <select id="config-modal-filter-status" class="config-filter-select">
                    <option value="all">All</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </div>
            <div class="config-filter-group">
                <label for="config-modal-filter-severity">Severity:</label>
                <select id="config-modal-filter-severity" class="config-filter-select">
                    <option value="all">All</option>
                    <option value="action">Action</option>
                    <option value="advice">Advice</option>
                </select>
            </div>
        `;
    },

    /**
     * Generates HTML for the Summary Cards
     */
    summary(enabled, disabled, total) {
        return `
            <div class="config-summary-grid">
                <div class="summary-card enabled"><div class="summary-number">${enabled}</div><div class="summary-label">Enabled Rules</div></div>
                <div class="summary-card disabled"><div class="summary-number">${disabled}</div><div class="summary-label">Disabled Rules</div></div>
                <div class="summary-card total"><div class="summary-number">${total}</div><div class="summary-label">Total Rules</div></div>
            </div>
        `;
    },

    /**
     * Generates HTML for a schema-driven settings form
     * @param {Object} schema - The settings_schema from the rule (AVAILABLE_SETTINGS)
     * @param {Object} currentValues - The current custom_settings values
     * @returns {string} HTML for the settings form
     */
    generateSettingsForm(schema, currentValues) {
        if (!schema || Object.keys(schema).length === 0) {
            // Fallback: return empty form or raw JSON textarea
            return '<div class="settings-form"><p class="text-slate-400 text-sm">No settings available</p></div>';
        }

        let formHtml = '<div class="settings-form">';
        
        for (const [key, meta] of Object.entries(schema)) {
            const type = meta.type || 'string';
            const description = meta.description || '';
            const currentValue = currentValues[key];
            
            // Title case the key for display
            const label = key.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
            ).join(' ');
            
            formHtml += '<div class="setting-group">';
            formHtml += `<div class="setting-label">${label}</div>`;
            if (description) {
                formHtml += `<div class="setting-description">${description}</div>`;
            }
            
            // Render input based on type
            if (type === 'bool') {
                const checked = currentValue === true ? 'checked' : '';
                formHtml += `<input type="checkbox" class="setting-checkbox" data-key="${key}" ${checked} />`;
            } else if (type === 'int') {
                const value = currentValue !== undefined ? currentValue : (meta.default || '');
                formHtml += `<input type="number" class="setting-input" data-key="${key}" value="${value}" min="0" />`;
            } else if (type === 'list') {
                // Join array values with newlines for display
                const listValue = Array.isArray(currentValue) 
                    ? currentValue.join('\n') 
                    : (Array.isArray(meta.default) ? meta.default.join('\n') : '');
                formHtml += `<textarea class="setting-list-input" rows="4" data-key="${key}" placeholder="Enter one value per line&#10;Example:&#10;value1&#10;value2&#10;value3">${listValue}</textarea>`;
                formHtml += `<div class="setting-hint">Enter one value per line</div>`;
            } else if (type === 'dict' || type === 'object') {
                // Fallback: raw JSON textarea for complex types
                const jsonValue = currentValue !== undefined 
                    ? JSON.stringify(currentValue, null, 2) 
                    : (meta.default ? JSON.stringify(meta.default, null, 2) : '{}');
                formHtml += `<textarea class="rule-settings-json" data-key="${key}" rows="6">${jsonValue}</textarea>`;
                formHtml += `<div class="setting-description">Raw JSON (complex type)</div>`;
            } else {
                // Default: string or unknown type
                const value = currentValue !== undefined ? String(currentValue) : (meta.default || '');
                formHtml += `<input type="text" class="setting-input" data-key="${key}" value="${value}" />`;
            }
            
            formHtml += '</div>';
        }
        
        formHtml += '</div>';
        return formHtml;
    },

    /**
     * Column-header strip rendered above the list of rule rows. Skipped for
     * built-in (read-only) configs where the per-row controls aren't shown.
     */
    ruleListHeader(isBuiltIn) {
        if (isBuiltIn) return '';
        return `
            <div class="rule-list-header" aria-hidden="false">
                <div class="rule-list-header-name">Rule</div>
                <div class="rule-list-header-controls">
                    <div class="rule-list-header-col rule-list-header-configure">Settings</div>
                    <div class="rule-list-header-col rule-list-header-severity">Severity</div>
                    <div class="rule-list-header-col rule-list-header-fix-strategy">Agent Fix Strategy</div>
                    <div class="rule-list-header-col rule-list-header-toggle">Enabled</div>
                </div>
            </div>
        `;
    },

    /**
     * Generates HTML for a single Rule Row
     */
    ruleRow({ ruleName, ruleConfig, isBuiltIn, supportsConfig }) {
        const isEnabled = ruleConfig.enabled;
        // Use helper logic passed in or calculated here.
        // For simplicity, we assume severity override logic is handled before passing data or simple check here
        const severity = ruleConfig.severity_override || 'ADVICE';
        const fixStrategy = ruleConfig.fix_strategy_override || 'design_decision';

        const customSettings = ruleConfig.custom_settings || {};
        const settingsText = Object.keys(customSettings).length > 0 ? JSON.stringify(customSettings, null, 2) : '';
        const isGhost = ruleConfig._is_ghost === true;

        const enabledClass = isEnabled ? 'enabled' : 'disabled';
        const ghostClass = isGhost ? 'ghost-rule' : '';

        const hasCustomSettings = Object.keys(customSettings).length > 0;
        const configureIcon = '🛠️';
        const configureText = 'Customize';

        return `
            <div class="rule-item ${enabledClass} ${ghostClass}" data-rule="${ruleName}">
                <div class="rule-row-header">
                    <div class="rule-name-container">
                        <div class="rule-name">
                            ${ruleName}
                            ${ruleConfig.documentation && Object.keys(ruleConfig.documentation).length > 0 ? `<button class="rule-info-btn" data-rule="${ruleName}" type="button" title="Open Grimoire Entry">📜</button>` : ''}
                            ${isGhost ? '<span class="ghost-warning-badge-inline">⚠️ Rule not found in runtime (not counted or used)</span>' : ''}
                        </div>
                    </div>
                    <div class="rule-controls-container">
                        ${!isBuiltIn && !isGhost ? `
                            ${supportsConfig ? `
                                <button class="rule-configure-btn ${hasCustomSettings ? 'modified' : ''}" data-rule="${ruleName}" type="button">
                                    ${configureIcon} ${configureText} <span class="configure-chevron" data-rule="${ruleName}">▼</span>
                                </button>
                            ` : ''}
                            <select class="rule-severity-select rule-severity-${severity.toLowerCase()}" data-rule="${ruleName}" data-severity="${severity}">
                                <option value="ADVICE" ${severity === 'ADVICE' ? 'selected' : ''}>ADVICE</option>
                                <option value="ACTION" ${severity === 'ACTION' ? 'selected' : ''}>ACTION</option>
                            </select>
                            <select class="rule-fix-strategy-select rule-fix-strategy-${fixStrategy}" data-rule="${ruleName}" data-fix-strategy="${fixStrategy}" title="Fix strategy: how amenable this rule's findings are to automated fixing by an AI agent">
                                <option value="mechanical" ${fixStrategy === 'mechanical' ? 'selected' : ''}>mechanical</option>
                                <option value="localized" ${fixStrategy === 'localized' ? 'selected' : ''}>localized</option>
                                <option value="naming_required" ${fixStrategy === 'naming_required' ? 'selected' : ''}>naming_required</option>
                                <option value="cascading_rename" ${fixStrategy === 'cascading_rename' ? 'selected' : ''}>cascading_rename</option>
                                <option value="design_decision" ${fixStrategy === 'design_decision' ? 'selected' : ''}>design_decision</option>
                            </select>
                        ` : ''}
                        ${!isBuiltIn && isGhost ? `<button class="rule-delete-btn" data-rule="${ruleName}" type="button" title="Remove ghost rule">🗑️ Remove</button>` : ''}
                        ${!isBuiltIn ? `
                            <div class="rule-toggle-switch ${isGhost ? 'disabled' : (isEnabled ? 'enabled' : 'disabled')}" data-rule="${ruleName}" ${isGhost ? 'disabled' : ''}>
                                <div class="toggle-track"><span class="toggle-thumb"></span></div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                ${!isBuiltIn && !isGhost && supportsConfig ? `
                    <div class="rule-settings-panel" data-rule="${ruleName}">
                        ${this.generateSettingsForm(ruleConfig.settings_schema, customSettings)}
                        <div class="rule-settings-error" data-rule="${ruleName}" style="display: none;">Invalid JSON format</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
};