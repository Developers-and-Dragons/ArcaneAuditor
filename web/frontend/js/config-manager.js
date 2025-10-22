// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    constructor(app) {
        this.app = app;
        this.availableConfigs = [];
        this.selectedConfig = getLastSelectedConfig();
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/configs');
            const data = await response.json();
            this.availableConfigs = data.configs;
            
            // If no config is selected, select the first available one
            if (!this.selectedConfig && this.availableConfigs.length > 0) {
                this.selectedConfig = this.availableConfigs[0].id;
                saveSelectedConfig(this.selectedConfig);
            }
            
            this.renderConfigurations();
        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.app.showError('Failed to load configurations. Please refresh the page.');
        }
    }

    renderConfigurations() {
        const configGrid = document.getElementById('config-grid');
        configGrid.innerHTML = '';

        // Group configurations by type
        const configGroups = {
            'Built-in': [],
            'Team': [],
            'Personal': []
        };

        this.availableConfigs.forEach(config => {
            const configType = config.type || 'Built-in';
            if (configGroups[configType]) {
                configGroups[configType].push(config);
            }
        });

        // Sort each group to put selected config first
        Object.keys(configGroups).forEach(groupName => {
            configGroups[groupName].sort((a, b) => {
                if (a.id === this.selectedConfig) return -1;
                if (b.id === this.selectedConfig) return 1;
                return 0;
            });
        });

        // Render each group in original order
        Object.entries(configGroups).forEach(([groupName, configs]) => {
            if (configs.length === 0) return;

            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'config-section';
            
            const sectionTitle = document.createElement('h4');
            sectionTitle.textContent = groupName;
            sectionDiv.appendChild(sectionTitle);

            const groupGrid = document.createElement('div');
            groupGrid.className = 'config-grid';

            configs.forEach(config => {
                const configElement = document.createElement('div');
                configElement.className = 'config-option';
                if (config.id === this.selectedConfig) {
                    configElement.classList.add('selected');
                }
                
                const isSelected = config.id === this.selectedConfig;
                const canEdit = config.source === 'personal' || config.source === 'teams';
                configElement.innerHTML = `
                    <div class="config-type ${config.type?.toLowerCase() || 'built-in'}">${config.type || 'Built-in'}</div>
                    <div class="config-name">${config.name}</div>
                    <div class="config-description">${config.description}</div>
                    <div class="config-meta">
                        <span class="config-rules-count">${config.rules_count} rules</span>
                        <span class="config-performance ${config.performance.toLowerCase()}">${config.performance}</span>
                    </div>
                    ${isSelected ? `
                        <div class="config-actions">
                            <button class="btn btn-secondary config-details-btn" onclick="showConfigBreakdown()">
                                📋 View Details
                            </button>
                            ${canEdit ? `
                                <button class="btn btn-primary config-edit-btn" onclick="showConfigEditor()">
                                    ✏️ Edit
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                `;
                
                configElement.addEventListener('click', () => this.selectConfiguration(config.id));
                groupGrid.appendChild(configElement);
            });

            sectionDiv.appendChild(groupGrid);
            configGrid.appendChild(sectionDiv);
        });
    }

    selectConfiguration(configId) {
        this.selectedConfig = configId;
        saveSelectedConfig(configId);
        // Don't re-render configurations to avoid jumping behavior
        // Just update the visual selection state
        this.updateConfigSelection();
    }

    updateConfigSelection() {
        // Update visual selection without re-rendering the entire grid
        const configElements = document.querySelectorAll('.config-option');
        configElements.forEach(element => {
            element.classList.remove('selected');
            // Remove any existing config-actions
            const existingActions = element.querySelector('.config-actions');
            if (existingActions) {
                existingActions.remove();
            }
        });

        // Find and select the clicked config
        const selectedElement = Array.from(configElements).find(element => {
            const configName = element.querySelector('.config-name').textContent;
            const config = this.availableConfigs.find(c => c.name === configName);
            return config && config.id === this.selectedConfig;
        });

        if (selectedElement) {
            selectedElement.classList.add('selected');
            
            // Add config actions to selected element
            const selectedConfig = this.availableConfigs.find(c => c.id === this.selectedConfig);
            if (selectedConfig) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'config-actions';
                const canEdit = selectedConfig.source === 'personal' || selectedConfig.source === 'teams';
                actionsDiv.innerHTML = `
                    <button class="btn btn-secondary config-details-btn" onclick="showConfigBreakdown()">
                        📋 View Details
                    </button>
                    ${canEdit ? `
                        <button class="btn btn-primary config-edit-btn" onclick="showConfigEditor()">
                            ✏️ Edit
                        </button>
                    ` : ''}
                `;
                selectedElement.appendChild(actionsDiv);
            }
        }
    }

    showConfigBreakdown() {
        const modal = document.getElementById('config-breakdown-modal');
        const content = document.getElementById('config-breakdown-content');
        
        if (!this.selectedConfig) {
            alert('Please select a configuration first');
            return;
        }
        
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) {
            alert('Configuration not found');
            return;
        }
        
        const rules = config.rules || {};
        const enabledRules = Object.entries(rules).filter(([_, ruleConfig]) => ruleConfig.enabled);
        const disabledRules = Object.entries(rules).filter(([_, ruleConfig]) => !ruleConfig.enabled);
        
        let html = `
            <div class="config-breakdown-section">
                <h4>📊 Configuration: ${config.name}</h4>
                <div class="config-summary-grid">
                    <div class="summary-card enabled">
                        <div class="summary-number">${enabledRules.length}</div>
                        <div class="summary-label">Enabled Rules</div>
                    </div>
                    <div class="summary-card disabled">
                        <div class="summary-number">${disabledRules.length}</div>
                        <div class="summary-label">Disabled Rules</div>
                    </div>
                    <div class="summary-card total">
                        <div class="summary-number">${Object.keys(rules).length}</div>
                        <div class="summary-label">Total Rules</div>
                    </div>
                </div>
            </div>
        `;
        
        if (enabledRules.length > 0) {
            html += `
                <div class="config-breakdown-section">
                    <h4>✅ Enabled Rules</h4>
                    <div class="rule-breakdown">
            `;
            
            enabledRules.forEach(([ruleName, ruleConfig]) => {
                const severity = ruleConfig.severity_override || 'ADVICE';
                const customSettings = ruleConfig.custom_settings || {};
                const settingsText = Object.keys(customSettings).length > 0 
                    ? JSON.stringify(customSettings, null, 2) 
                    : '';
                
                html += `
                    <div class="rule-item enabled">
                        <div class="rule-header-row">
                            <div class="rule-name">${ruleName}</div>
                        </div>
                        <div class="rule-description">Severity: ${severity}</div>
                        ${settingsText ? `
                            <div class="rule-settings">
                                <div class="settings-label">Custom Settings:</div>
                                <pre class="settings-json">${settingsText}</pre>
                            </div>
                        ` : ''}
                        <div class="rule-status-badge enabled">✓ Enabled</div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        if (disabledRules.length > 0) {
            html += `
                <div class="config-breakdown-section">
                    <h4>❌ Disabled Rules</h4>
                    <div class="rule-breakdown">
            `;
            
            disabledRules.forEach(([ruleName, ruleConfig]) => {
                const severity = ruleConfig.severity_override || 'ADVICE';
                html += `
                    <div class="rule-item disabled">
                        <div class="rule-header-row">
                            <div class="rule-name">${ruleName}</div>
                        </div>
                        <div class="rule-description">Severity: ${severity}</div>
                        <div class="rule-status-badge disabled">✗ Disabled</div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        content.innerHTML = html;
        
        modal.style.display = 'flex';
    }

    // Theme management
    initializeTheme() {
        // Check for saved theme preference or default to dark mode
        const savedTheme = localStorage.getItem('arcane-auditor-theme') || 'dark';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Cast Light';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Cast Darkness';
        }
        
        // Save preference
        localStorage.setItem('arcane-auditor-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    showConfigEditor() {
        const modal = document.getElementById('config-editor-modal');
        const content = document.getElementById('config-editor-content');

        if (!this.selectedConfig) {
            alert('Please select a configuration first');
            return;
        }

        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) {
            alert('Configuration not found');
            return;
        }

        // Check if config is editable
        if (config.source !== 'personal' && config.source !== 'teams') {
            alert('Built-in preset configurations cannot be edited. Create a personal or team configuration instead.');
            return;
        }

        const rules = config.rules || {};

        // Create editor UI with search and filter
        let html = `
            <div class="config-editor-header">
                <h4>Editing: ${config.name}</h4>
                <div class="editor-controls">
                    <input type="text" id="rule-search" class="search-input" placeholder="🔍 Search rules..." />
                    <select id="rule-filter" class="filter-select">
                        <option value="all">All Rules</option>
                        <option value="enabled">Enabled Only</option>
                        <option value="disabled">Disabled Only</option>
                        <option value="custom">Has Custom Settings</option>
                    </select>
                </div>
            </div>
            <div class="rules-editor-container" id="rules-editor-container">
        `;

        // Sort rules alphabetically
        const sortedRules = Object.entries(rules).sort((a, b) => a[0].localeCompare(b[0]));

        sortedRules.forEach(([ruleName, ruleConfig]) => {
            const enabled = ruleConfig.enabled;
            const severity = ruleConfig.severity_override || 'ADVICE';
            const customSettings = ruleConfig.custom_settings || {};
            const hasCustomSettings = Object.keys(customSettings).length > 0;

            html += `
                <div class="rule-editor-item" data-rule-name="${ruleName}" data-enabled="${enabled}" data-has-custom="${hasCustomSettings}">
                    <div class="rule-editor-header">
                        <div class="rule-toggle-container">
                            <label class="toggle-switch">
                                <input type="checkbox"
                                    class="rule-toggle"
                                    data-rule="${ruleName}"
                                    ${enabled ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                            <div class="rule-info">
                                <div class="rule-name-editor">${ruleName}</div>
                                <div class="rule-status-text ${enabled ? 'enabled' : 'disabled'}">
                                    ${enabled ? '✓ Enabled' : '✗ Disabled'}
                                </div>
                            </div>
                        </div>
                        <button class="btn btn-small expand-settings-btn" onclick="toggleRuleSettings('${ruleName}')">
                            ${hasCustomSettings ? '⚙️' : '+'} Settings
                        </button>
                    </div>
                    <div class="rule-settings-panel" id="settings-${ruleName}" style="display: none;">
                        <div class="setting-group">
                            <label>Severity Override:</label>
                            <select class="severity-select" data-rule="${ruleName}">
                                <option value="ACTION" ${severity === 'ACTION' ? 'selected' : ''}>ACTION</option>
                                <option value="ADVICE" ${severity === 'ADVICE' ? 'selected' : ''}>ADVICE</option>
                            </select>
                        </div>
                        <div class="setting-group">
                            <label>Custom Settings (JSON):</label>
                            <textarea
                                class="custom-settings-input"
                                data-rule="${ruleName}"
                                rows="4"
                                placeholder="{}">${JSON.stringify(customSettings, null, 2)}</textarea>
                            <small class="setting-hint">Enter valid JSON for rule-specific settings</small>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div>`;

        content.innerHTML = html;
        modal.style.display = 'flex';

        // Add event listeners for search and filter
        document.getElementById('rule-search').addEventListener('input', this.filterRules.bind(this));
        document.getElementById('rule-filter').addEventListener('change', this.filterRules.bind(this));

        // Add event listeners for rule toggles to update status text
        document.querySelectorAll('.rule-toggle').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const ruleItem = e.target.closest('.rule-editor-item');
                const statusText = ruleItem.querySelector('.rule-status-text');
                if (e.target.checked) {
                    statusText.textContent = '✓ Enabled';
                    statusText.className = 'rule-status-text enabled';
                    ruleItem.dataset.enabled = 'true';
                } else {
                    statusText.textContent = '✗ Disabled';
                    statusText.className = 'rule-status-text disabled';
                    ruleItem.dataset.enabled = 'false';
                }
            });
        });
    }

    filterRules() {
        const searchTerm = document.getElementById('rule-search').value.toLowerCase();
        const filterValue = document.getElementById('rule-filter').value;
        const ruleItems = document.querySelectorAll('.rule-editor-item');

        ruleItems.forEach(item => {
            const ruleName = item.dataset.ruleName.toLowerCase();
            const isEnabled = item.dataset.enabled === 'true';
            const hasCustomSettings = item.dataset.hasCustom === 'true';

            let matchesSearch = ruleName.includes(searchTerm);
            let matchesFilter = true;

            switch(filterValue) {
                case 'enabled':
                    matchesFilter = isEnabled;
                    break;
                case 'disabled':
                    matchesFilter = !isEnabled;
                    break;
                case 'custom':
                    matchesFilter = hasCustomSettings;
                    break;
            }

            if (matchesSearch && matchesFilter) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    async saveConfigChanges() {
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) {
            alert('Configuration not found');
            return;
        }

        // Collect updated rule settings
        const updatedRules = {};
        document.querySelectorAll('.rule-editor-item').forEach(item => {
            const ruleName = item.dataset.ruleName;
            const toggle = item.querySelector('.rule-toggle');
            const severitySelect = item.querySelector('.severity-select');
            const customSettingsInput = item.querySelector('.custom-settings-input');

            let customSettings = {};
            try {
                const settingsText = customSettingsInput.value.trim();
                if (settingsText) {
                    customSettings = JSON.parse(settingsText);
                }
            } catch (e) {
                alert(`Invalid JSON in custom settings for ${ruleName}: ${e.message}`);
                throw e;
            }

            updatedRules[ruleName] = {
                enabled: toggle.checked,
                severity_override: severitySelect.value,
                custom_settings: customSettings
            };
        });

        // Build the complete config object
        const updatedConfig = {
            rules: updatedRules,
            file_processing: config.file_processing || {},
            output: config.output || {},
            fail_on_error: config.fail_on_error || false,
            fail_on_warning: config.fail_on_warning || false,
            quiet: config.quiet || false
        };

        try {
            const response = await fetch(`/api/configs/${config.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedConfig)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save configuration');
            }

            const result = await response.json();
            alert('Configuration saved successfully!');

            // Hide the editor modal
            window.hideConfigEditor();

            // Reload configurations to reflect changes
            await this.loadConfigurations();

        } catch (error) {
            console.error('Error saving configuration:', error);
            alert(`Failed to save configuration: ${error.message}`);
        }
    }
}

// Global function for HTML onclick handlers
window.showConfigBreakdown = function() {
    if (window.app && window.app.configManager) {
        window.app.configManager.showConfigBreakdown();
    }
};

window.hideConfigBreakdown = function() {
    const modal = document.getElementById('config-breakdown-modal');
    if (modal) {
        modal.style.display = 'none';
    }
};

window.showConfigEditor = function() {
    if (window.app && window.app.configManager) {
        window.app.configManager.showConfigEditor();
    }
};

window.hideConfigEditor = function() {
    const modal = document.getElementById('config-editor-modal');
    if (modal) {
        modal.style.display = 'none';
    }
};

window.toggleRuleSettings = function(ruleName) {
    const panel = document.getElementById(`settings-${ruleName}`);
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
};

window.saveConfigChanges = function() {
    if (window.app && window.app.configManager) {
        window.app.configManager.saveConfigChanges();
    }
};

// Close modals when clicking outside
document.addEventListener('click', function(event) {
    const breakdownModal = document.getElementById('config-breakdown-modal');
    const editorModal = document.getElementById('config-editor-modal');

    if (event.target === breakdownModal) {
        window.hideConfigBreakdown();
    }
    if (event.target === editorModal) {
        window.hideConfigEditor();
    }
});

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        window.hideConfigBreakdown();
        window.hideConfigEditor();
    }
});
