// ui-breakdown.js
import { ConfigAPI } from './api.js';
import { Templates } from './templates.js';
import { GrimoireUI } from './grimoire.js';
import { SettingsHandler } from './settings-logic.js';

export class ConfigBreakdownUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
        
        // Store current state for filtering
        this.currentConfig = null;
        this.currentIsBuiltIn = false;
        this.allRules = [];
        
        // Store filter state to persist across refreshes
        this.savedFilterState = {
            search: '',
            status: 'all',
            severity: 'all'
        };
        
        // Flag to track if we're reloading after a save (to persist filters)
        this.isReloadingAfterSave = false;
        
        // Track if events are bound to avoid duplicates
        this.eventsBound = false;
        
        // Track if a ghost rule deletion is in progress
        this.isDeletingGhostRule = false;
        
        // Initialize helper classes
        this.grimoire = new GrimoireUI();
        this.settingsHandler = new SettingsHandler();
        
        // Keep settings handler in sync with current config
        this.settingsHandler.setCurrentConfig = (config) => {
            this.settingsHandler.currentConfig = config;
        };

        // Escape key functionality (only close config modal if Grimoire is not open)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Check if Grimoire modal is open - if so, don't close config modal
                const grimoireModal = document.getElementById('grimoire-modal');
                if (grimoireModal && grimoireModal.style.display !== 'none' && grimoireModal.style.display !== '') {
                    return; // Grimoire is open, let it handle the Escape key
                }
                this.hide();
            }
        });
    }

    /**
     * Helper to close the modal
     */
    hide() {
        // Reset filter state and reload flag when closing modal
        this.savedFilterState = {
            search: '',
            status: 'all',
            severity: 'all'
        };
        this.isReloadingAfterSave = false;
        
        const modal = document.getElementById('config-breakdown-modal');
        if (modal) modal.style.display = 'none';
    }

    /**
     * The main method to show the breakdown modal
     */
    show(configId) {
        // Reset filter state only if this is a fresh open (not a reload after save)
        if (!this.isReloadingAfterSave) {
            this.savedFilterState = {
                search: '',
                status: 'all',
                severity: 'all'
            };
        }
        
        const modal = document.getElementById('config-breakdown-modal');
        if (!modal) {
            this.app.showToast('Configuration modal not found', 'error');
            return;
        }
        
        const content = document.getElementById('config-breakdown-content');
        if (!content) {
            this.app.showToast('Configuration modal content not found', 'error');
            return;
        }
        
        // Find header within the modal (not document-wide)
        const modalContent = modal.querySelector('.modal-content');
        if (!modalContent) {
            this.app.showToast('Configuration modal structure invalid', 'error');
            return;
        }
        
        let header = modalContent.querySelector('.modal-header');
        
        // Create header if it doesn't exist (shouldn't happen, but be defensive)
        if (!header) {
            header = document.createElement('div');
            header.className = 'modal-header';
            modalContent.insertBefore(header, content);
        }
        
        // Access data from the manager
        const config = this.manager.availableConfigs.find(c => c.id === configId);
        
        if (!config) {
            this.app.showToast('Configuration not found', 'error');
            return;
        }
        
        // Check if config is built-in
        const category = (config.category || config.type || '').toLowerCase();
        const isBuiltIn = category === 'built-in' || category === 'builtin';
        const sourceName = isBuiltIn ? 'Built-in' : (category === 'team' ? 'Team' : 'Personal');
        
        // --- 1. RENDER HEADER ---
        {
            header.innerHTML = '';
            
            // Left: Title + Badge
            const leftSide = document.createElement('div');
            leftSide.className = 'modal-header-left';
            leftSide.innerHTML = `
                <h3 class="modal-title">${config.name}</h3>
                <span class="config-source-badge">${sourceName}</span>
                ${isBuiltIn ? '<span class="config-readonly-badge">Read-only</span>' : ''}
            `;
            
            // Right: Action Bar
            const rightSide = document.createElement('div');
            rightSide.className = 'modal-header-right';
            
            let actionButtons = '';
            
            // Delete (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="delete-config" class="modal-action-btn delete-btn" title="Delete configuration">🗑️</button>`;
            }
            
            // Duplicate (always)
            actionButtons += `<button id="duplicate-config" class="modal-action-btn duplicate-btn" title="Duplicate configuration">🪄</button>`;
            
            // Save (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="save-config" class="modal-action-btn save-btn" title="Save changes">💾 Save</button>`;
            }
            
            actionButtons += `<div class="modal-action-separator"></div>`;
            actionButtons += `<button id="close-config" class="modal-close" title="Close">×</button>`;
            
            rightSide.innerHTML = actionButtons;
            header.appendChild(leftSide);
            header.appendChild(rightSide);

            // Bind Header Events
            const delBtn = header.querySelector('#delete-config');
            const dupBtn = header.querySelector('#duplicate-config');
            const saveBtn = header.querySelector('#save-config');
            const closeBtn = header.querySelector('#close-config');

            if (delBtn) delBtn.onclick = () => {
                this.manager.requestDeleteConfiguration(config);
                modal.style.display = 'none';
            };
            if (dupBtn) dupBtn.onclick = () => {
                modal.style.display = 'none';
                this.manager.openDuplicateModal(config.id, 'Personal');
            };
            if (saveBtn) saveBtn.onclick = () => {
                // Save filter state and set flag before refreshing (so it persists during save/refresh cycle)
                this.saveFilterState();
                this.isReloadingAfterSave = true;
                this.manager.saveCurrentConfigChanges(config);
            };
            if (closeBtn) closeBtn.onclick = () => this.hide();
        }
        
        // Store current state for filtering
        this.currentConfig = config;
        this.currentIsBuiltIn = isBuiltIn;
        
        // Sync settings handler with current config
        if (this.settingsHandler) {
            this.settingsHandler.currentConfig = config;
        }
        
        // --- 2. RENDER BODY (Rules) ---
        this.renderBody(config, isBuiltIn, content);
        
        // --- 3. RENDER FILTER TOOLBAR (after body so it's in the right place) ---
        this.renderFilterToolbar(content);
        
        // --- 4. RESTORE FILTER STATE (if reloading after save) ---
        if (this.isReloadingAfterSave) {
            this.restoreFilterState(content);
            this.isReloadingAfterSave = false; // Reset flag after restoring
        }
        
        // --- 5. BIND GRIMOIRE EVENTS (Always - viewing docs doesn't require edit permissions) ---
        this.bindGrimoireEvents(content);
        
        // --- 6. BIND EVENTS (Only if not built-in) ---
        if (!isBuiltIn) {
            this.bindRuleEvents(content, config);
        }
        
        // --- 7. BIND FILTER EVENTS ---
        this.bindFilterEvents(content, config);
        
        modal.style.display = 'flex';
    }

    /**
     * Render the filter toolbar below the summary section
     */
    renderFilterToolbar(content) {
        // Remove existing toolbar if present
        const existingToolbar = content.querySelector('.config-filter-toolbar');
        if (existingToolbar) {
            existingToolbar.remove();
        }
        
        const toolbar = document.createElement('div');
        toolbar.className = 'config-filter-toolbar';
        toolbar.innerHTML = Templates.filterToolbar();
        
        // Insert after the summary section (first config-breakdown-section)
        const summarySection = content.querySelector('.config-breakdown-section');
        if (summarySection && summarySection.nextSibling) {
            content.insertBefore(toolbar, summarySection.nextSibling);
        } else if (summarySection) {
            summarySection.insertAdjacentElement('afterend', toolbar);
        } else {
            content.appendChild(toolbar);
        }
    }

    /**
     * Get the effective severity for a rule (checks override first, then defaults to ADVICE)
     */
    getRuleSeverity(ruleConfig) {
        // Check severity_override first
        if (ruleConfig.severity_override) {
            return ruleConfig.severity_override;
        }
        // Default to ADVICE if no override
        return 'ADVICE';
    }

    /**
     * Filter rules based on search and filter criteria
     */
    filterRules(allRules, searchTerm, statusFilter, severityFilter) {
        return allRules.filter(([ruleName, ruleConfig]) => {
            // Search filter
            if (searchTerm) {
                const searchLower = searchTerm.toLowerCase();
                if (!ruleName.toLowerCase().includes(searchLower)) {
                    return false;
                }
            }
            
            // Status filter
            if (statusFilter !== 'all') {
                const isEnabled = ruleConfig.enabled && !ruleConfig._is_ghost;
                if (statusFilter === 'enabled' && !isEnabled) return false;
                if (statusFilter === 'disabled' && isEnabled) return false;
            }
            
            // Severity filter
            if (severityFilter !== 'all') {
                const severity = this.getRuleSeverity(ruleConfig);
                if (severity.toLowerCase() !== severityFilter.toLowerCase()) {
                    return false;
                }
            }
            
            return true;
        });
    }

    renderBody(config, isBuiltIn, content) {
        const rules = config.rules || {};
        const enabledRules = Object.entries(rules).filter(([_, r]) => r.enabled && !r._is_ghost).length;
        const disabledRules = Object.entries(rules).filter(([_, r]) => !r.enabled && !r._is_ghost).length;
        const allRules = Object.entries(rules).sort(([a], [b]) => a.localeCompare(b));
        
        // Store allRules for filtering
        this.allRules = allRules;

        // Clear existing content
        content.innerHTML = '';

        // Summary section
        const summarySection = document.createElement('div');
        summarySection.className = 'config-breakdown-section';
        summarySection.innerHTML = Templates.summary(enabledRules, disabledRules, Object.keys(rules).length);
        content.appendChild(summarySection);

        // Filter toolbar will be inserted after summary section by renderFilterToolbar

        // Rules section
        const rulesSection = document.createElement('div');
        rulesSection.className = 'config-breakdown-section';
        rulesSection.innerHTML = `
            <h4>📋 Rules</h4>
            <div class="rule-breakdown"></div>
        `;
        content.appendChild(rulesSection);
        
        // Render the rules list
        const ruleBreakdown = rulesSection.querySelector('.rule-breakdown');
        this.renderRuleList(ruleBreakdown, allRules, isBuiltIn);
    }

    /**
     * Render the list of rules (used for initial render and filtered updates)
     * @param {HTMLElement} container - The container to render rules into
     * @param {Array} rulesToRender - Array of [ruleName, ruleConfig] tuples
     * @param {boolean} isBuiltIn - Whether this is a built-in config
     * @param {boolean} skipEventBinding - If true, skip binding events (for use during restore)
     */
    renderRuleList(container, rulesToRender, isBuiltIn, skipEventBinding = false) {
        if (!container) return;

        // Column header strip — labels every per-row control. Hidden for built-in configs
        // (read-only, no controls).
        const headerHtml = Templates.ruleListHeader(isBuiltIn);

        // Map the data to the template
        const rowsHtml = rulesToRender.map(([ruleName, ruleConfig]) => {
            return Templates.ruleRow({
                ruleName,
                ruleConfig,
                isBuiltIn,
                supportsConfig: ruleConfig.supports_config !== false
            });
        }).join('');

        container.innerHTML = headerHtml + rowsHtml;
        
        // Note: Events are bound by the caller (show() or bindFilterEvents)
        // We don't bind here to avoid double-binding and container issues
    }

    bindRuleEvents(content, config) {
        // PART 1: Bind Delegation Listeners (ONCE per container lifetime)
        // These are attached to the static container and handle clicks for dynamic children
        if (content.dataset.eventsBound !== 'true') {
            content.dataset.eventsBound = 'true';
            
            // Toggle Switches
            content.addEventListener('click', (e) => {
                const toggle = e.target.closest('.rule-toggle-switch:not([disabled])');
                if (toggle) {
                    e.stopPropagation();
                    const ruleName = toggle.dataset.rule;
                    const ruleItem = toggle.closest('.rule-item');
                    if (!ruleItem) return;
                    
                    const isCurrentlyEnabled = ruleItem.classList.contains('enabled');
                    
                    // Toggle UI state
                    ruleItem.classList.toggle('enabled', !isCurrentlyEnabled);
                    ruleItem.classList.toggle('disabled', isCurrentlyEnabled);
                    toggle.classList.toggle('enabled', !isCurrentlyEnabled);
                    toggle.classList.toggle('disabled', isCurrentlyEnabled);
                    
                    // Update Config Data - Use `this.currentConfig` to ensure we edit fresh data
                    if (this.currentConfig && this.currentConfig.rules && this.currentConfig.rules[ruleName]) {
                        this.currentConfig.rules[ruleName].enabled = !isCurrentlyEnabled;
                    }
                }
            });
            
            // Ghost Rule Deletion
            content.addEventListener('click', (e) => {
                const btn = e.target.closest('.rule-delete-btn');
                if (btn && !this.isDeletingGhostRule) {
                    e.stopPropagation();
                    e.preventDefault();
                    const ruleName = btn.dataset.rule;
                    
                    // Show custom modal instead of browser confirm
                    this.showGhostRuleDeleteModal(ruleName, btn, content);
                }
            });

            // Expand/Collapse Settings
            content.addEventListener('click', (e) => {
                const btn = e.target.closest('.rule-configure-btn');
                if (btn) {
                    e.stopPropagation();
                    const ruleName = btn.dataset.rule;
                    const panel = content.querySelector(`.rule-settings-panel[data-rule="${ruleName}"]`);
                    const chevron = btn.querySelector('.configure-chevron');
                    if (panel) {
                        panel.classList.toggle('expanded');
                        if (chevron) chevron.textContent = panel.classList.contains('expanded') ? '▲' : '▼';
                    }
                }
            });
            
        }
        
        // PART 2: Bind Direct Events (EVERY TIME content renders)
        // These elements are destroyed and recreated on every render, so they need fresh listeners
        this.bindDirectEvents(content, config || this.currentConfig);
    }
    
    /**
     * Bind Grimoire events (always - viewing docs doesn't require edit permissions)
     * @param {HTMLElement} content - The content container
     */
    bindGrimoireEvents(content) {
        // Use delegation to handle dynamically added Grimoire buttons
        if (content.dataset.grimoireBound !== 'true') {
            content.dataset.grimoireBound = 'true';
            
            // Grimoire Icon Click
            content.addEventListener('click', (e) => {
                const btn = e.target.closest('.rule-info-btn');
                if (btn) {
                    e.stopPropagation();
                    const ruleName = btn.dataset.rule;
                    this.grimoire.openedFromConfigModal = true;
                    this.grimoire.showGrimoire(ruleName, this.currentConfig);
                }
            });

            // Agent Fix Strategy help: in-memory toggle only. Always closed on each
            // page load — users who want to look can open it; we don't persist the
            // preference because the panel is unlikely to be wanted open by default.
            content.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.dataset.action;
                if (!action) return;
                const helpPanel = content.querySelector('[data-fix-strategy-help]');
                if (!helpPanel) return;
                if (action === 'toggle-fix-strategy-help') {
                    e.stopPropagation();
                    if (helpPanel.hasAttribute('hidden')) helpPanel.removeAttribute('hidden');
                    else helpPanel.setAttribute('hidden', '');
                } else if (action === 'dismiss-fix-strategy-help') {
                    e.stopPropagation();
                    helpPanel.setAttribute('hidden', '');
                }
            });
        }
    }
    
    /**
     * Bind direct events (severity dropdowns, textareas) that need individual binding
     * This is called after re-rendering rules to bind new DOM elements
     */
    bindDirectEvents(container, config) {
        // Use currentConfig to ensure we always edit fresh data
        const activeConfig = config || this.currentConfig;
        
        // Severity Dropdowns - direct binding (change events don't bubble the same way)
        container.querySelectorAll('.rule-severity-select:not([data-events-bound])').forEach(select => {
            // Mark as bound to prevent duplicate bindings
            select.dataset.eventsBound = 'true';

            select.addEventListener('change', (e) => {
                e.stopPropagation(); // Prevent event from bubbling and interfering with other handlers
                const ruleName = select.dataset.rule;
                const newSeverity = select.value;
                if (activeConfig && activeConfig.rules && activeConfig.rules[ruleName]) {
                    activeConfig.rules[ruleName].severity_override = newSeverity;
                }
                select.className = `rule-severity-select rule-severity-${newSeverity.toLowerCase()}`;
            });
        });

        // Fix-strategy dropdowns - same direct-binding pattern as severity.
        container.querySelectorAll('.rule-fix-strategy-select:not([data-events-bound])').forEach(select => {
            select.dataset.eventsBound = 'true';

            select.addEventListener('change', (e) => {
                e.stopPropagation();
                const ruleName = select.dataset.rule;
                const newStrategy = select.value;
                if (activeConfig && activeConfig.rules && activeConfig.rules[ruleName]) {
                    activeConfig.rules[ruleName].fix_strategy_override = newStrategy;
                }
                select.className = `rule-fix-strategy-select rule-fix-strategy-${newStrategy}`;
            });
        });

        // Delegate settings form events to SettingsHandler
        this.settingsHandler.bindSettingsFormEvents(container, activeConfig);
    }
    
    /**
     * Save current filter state
     */
    saveFilterState() {
        const content = document.getElementById('config-breakdown-content');
        if (!content) return;
        
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        
        this.savedFilterState = {
            search: searchInput ? searchInput.value.trim() : '',
            status: statusFilter ? statusFilter.value : 'all',
            severity: severityFilter ? severityFilter.value : 'all'
        };
    }

    /**
     * Restore saved filter state and apply filters
     */
    restoreFilterState(content) {
        if (!this.savedFilterState) return;
        
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        const ruleBreakdown = content.querySelector('.rule-breakdown');
        
        if (!ruleBreakdown) return;
        
        // Restore values
        if (searchInput && this.savedFilterState.search) {
            searchInput.value = this.savedFilterState.search;
        }
        if (statusFilter && this.savedFilterState.status !== 'all') {
            statusFilter.value = this.savedFilterState.status;
        }
        if (severityFilter && this.savedFilterState.severity !== 'all') {
            severityFilter.value = this.savedFilterState.severity;
        }
        
        // Apply filters if any are active
        if (this.savedFilterState.search || 
            this.savedFilterState.status !== 'all' || 
            this.savedFilterState.severity !== 'all') {
            const filteredRules = this.filterRules(
                this.allRules,
                this.savedFilterState.search,
                this.savedFilterState.status,
                this.savedFilterState.severity
            );
            this.renderRuleList(ruleBreakdown, filteredRules, this.currentIsBuiltIn, true);
            
            // Re-bind events after restoring filtered state (since elements were recreated)
            if (!this.currentIsBuiltIn && this.currentConfig) {
                this.bindRuleEvents(content, this.currentConfig);
            }
        }
    }

    /**
     * Bind event listeners for search and filter controls
     */
    bindFilterEvents(content, config) {
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        const ruleBreakdown = content.querySelector('.rule-breakdown');
        
        if (!ruleBreakdown) return;
        
        const applyFilters = () => {
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            const statusValue = statusFilter ? statusFilter.value : 'all';
            const severityValue = severityFilter ? severityFilter.value : 'all';
            
            // Save filter state whenever it changes
            this.savedFilterState = {
                search: searchTerm,
                status: statusValue,
                severity: severityValue
            };
            
            const filteredRules = this.filterRules(this.allRules, searchTerm, statusValue, severityValue);
            // Re-render the list (this clears and recreates elements, so we need to rebind)
            this.renderRuleList(ruleBreakdown, filteredRules, this.currentIsBuiltIn, true);
            
            // Re-bind events after filtering (since elements were recreated)
            if (!this.currentIsBuiltIn && this.currentConfig) {
                this.bindRuleEvents(content, this.currentConfig);
            }
        };
        
        if (searchInput) {
            searchInput.addEventListener('input', applyFilters);
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', applyFilters);
        }
        
        if (severityFilter) {
            severityFilter.addEventListener('change', applyFilters);
        }
    }

    /**
     * Show the ghost rule delete confirmation modal
     */
    showGhostRuleDeleteModal(ruleName, deleteBtn, content) {
        const modal = document.getElementById('ghost-rule-delete-modal');
        const message = document.getElementById('ghost-rule-delete-message');
        const confirmBtn = document.getElementById('ghost-rule-delete-confirm');
        const cancelBtn = document.getElementById('ghost-rule-delete-cancel');
        const closeBtn = document.getElementById('ghost-rule-delete-close');
        
        if (!modal || !message || !confirmBtn) {
            console.error('Ghost rule delete modal elements not found');
            return;
        }

        // Update message
        message.textContent = `Remove ghost rule "${ruleName}"? This rule is not found in the runtime and will not be counted or used.`;

        // Cleanup previous listeners to prevent memory leaks/double-clicks
        const cleanup = () => {
            confirmBtn.onclick = null;
            if (cancelBtn) cancelBtn.onclick = null;
            if (closeBtn) closeBtn.onclick = null;
            modal.hidden = true;
        };

        // Bind Confirm
        confirmBtn.onclick = () => {
            cleanup();
            this.handleGhostRuleDelete(ruleName, deleteBtn, content);
        };

        // Bind Cancel
        if (cancelBtn) {
            cancelBtn.onclick = cleanup;
        }

        // Bind Close
        if (closeBtn) {
            closeBtn.onclick = cleanup;
        }

        // Show modal
        modal.hidden = false;
    }

    /**
     * Handle the actual ghost rule deletion
     */
    async handleGhostRuleDelete(ruleName, deleteBtn, content) {
        if (this.isDeletingGhostRule) return;
        
        this.isDeletingGhostRule = true;
        try {
            // Delete from config object using currentConfig
            if (this.currentConfig && this.currentConfig.rules && this.currentConfig.rules[ruleName]) {
                delete this.currentConfig.rules[ruleName];
            }
            
            // Save the updated config
            await ConfigAPI.save(this.currentConfig);
            
            // Remove the DOM element immediately for better UX
            const ruleItem = deleteBtn.closest('.rule-item');
            if (ruleItem) {
                ruleItem.remove();
            }
            
            // Update the manager's config cache
            const managerConfig = this.manager.availableConfigs.find(c => c.id === this.currentConfig.id);
            if (managerConfig) {
                managerConfig.rules = this.currentConfig.rules;
            }
            
            // Re-render just the rules list without full modal refresh
            // This avoids rebinding events and breaking the UI
            const rulesContainer = content.querySelector('.rules-list');
            if (rulesContainer) {
                // Get fresh config data
                const updatedConfig = managerConfig || this.currentConfig;
                this.allRules = Object.entries(updatedConfig.rules || {})
                    .map(([name, ruleConfig]) => ({ name, ...ruleConfig }))
                    .sort((a, b) => a.name.localeCompare(b.name));
                
                // Re-render the rules list
                rulesContainer.innerHTML = '';
                this.renderRuleList(this.allRules, rulesContainer, updatedConfig, this.currentIsBuiltIn);
                
                // Re-bind events for the new DOM elements (severity dropdowns, textareas)
                // But don't rebind the click handlers since they use event delegation
                this.bindDirectEvents(rulesContainer, updatedConfig);
            }
            
            this.app.showToast('Ghost rule removed', 'success');
        } catch (error) {
            console.error('Error removing ghost rule:', error);
            this.app.showToast('Failed to remove ghost rule', 'error');
        } finally {
            this.isDeletingGhostRule = false;
        }
    }

    /**
     * Handle JSON blur for fallback dict/object types (legacy support)
     * This is only used for complex types that can't be represented as simple form inputs
     */

}