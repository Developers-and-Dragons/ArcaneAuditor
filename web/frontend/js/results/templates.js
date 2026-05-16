// results/templates.js - Pure HTML template functions

import { 
    getSeverityIcon, 
    getSeverityCounts, 
    getOrderedSeverityEntries,
    getFileTypeFromPath,
    groupFindingsByFile,
    sortFindingsInGroup,
    sortFileGroups
} from '../utils.js';

export const Templates = {
    /**
     * Generates HTML for the summary section
     * @param {Object} result - The current result object
     * @param {string} uploadedFileName - The name of the uploaded file
     * @returns {string} HTML for the summary
     */
    summary(result, uploadedFileName) {
        const severityCounts = getSeverityCounts(result.findings);
        
        return `
            <h4>📈 Summary</h4>
            ${uploadedFileName ? `
                <div class="summary-filename-section">
                    <div class="summary-filename">📁 ${uploadedFileName}</div>
                    <div class="summary-filename-label">Analyzed Application</div>
                </div>
            ` : ''}
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-number summary-number-blue">${result.summary?.total_findings || result.findings.length}</div>
                    <div class="summary-label">Issues Found</div>
                </div>
                <div class="summary-item">
                    <div class="summary-number summary-number-purple">${result.summary?.rules_executed || 0}</div>
                    <div class="summary-label">Rules Enabled</div>
                </div>
                <div class="summary-item magic-summary-card action">
                    <div class="count">${result.summary?.by_severity?.action || 0}</div>
                    <div class="label">
                        <span class="icon">${getSeverityIcon('ACTION')}</span> Actions
                    </div>
                </div>
                <div class="summary-item magic-summary-card advice">
                    <div class="count">${result.summary?.by_severity?.advice || 0}</div>
                    <div class="label">
                        <span class="icon">${getSeverityIcon('ADVICE')}</span> Advices
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Generates HTML for the findings container with filters
     * @param {Object} filters - Current filter state
     * @param {Object} sortOptions - Current sort options
     * @returns {string} HTML for the findings container
     */
    findingsContainer(filters, sortOptions) {
        return `
            <div class="findings-header">
                <div class="expand-collapse-buttons">
                    <button class="btn btn-secondary" onclick="app.expandAllFiles()">Expand All</button>
                    <button class="btn btn-secondary" onclick="app.collapseAllFiles()">Collapse All</button>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <div class="micro-label">Severity</div>
                        <select id="severity-filter" onchange="app.updateSeverityFilter(this.value)">
                            <!-- Options will be populated dynamically by updateFilterOptions() -->
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">File Type</div>
                        <select id="file-type-filter" onchange="app.updateFileTypeFilter(this.value)">
                            <!-- Options will be populated dynamically by updateFilterOptions() -->
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">File Order</div>
                        <select id="sort-files-by" onchange="app.updateSortFilesBy(this.value)">
                            <option value="alphabetical" ${sortOptions.sortFilesBy === 'alphabetical' ? 'selected' : ''}>File Name</option>
                            <option value="issue-count" ${sortOptions.sortFilesBy === 'issue-count' ? 'selected' : ''}>Issue Count</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">Issue Order</div>
                        <select id="sort-by" onchange="app.updateSortBy(this.value)">
                            <option value="severity" ${sortOptions.sortBy === 'severity' ? 'selected' : ''}>Severity</option>
                            <option value="line" ${sortOptions.sortBy === 'line' ? 'selected' : ''}>Line Number</option>
                            <option value="rule" ${sortOptions.sortBy === 'rule' ? 'selected' : ''}>Rule ID</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="findings-content">
                <!-- File groups will be inserted here -->
            </div>
        `;
    },

    /**
     * Generates HTML for a file group
     * @param {string} filePath - The file path
     * @param {Array} fileFindings - Array of findings for this file
     * @param {boolean} isExpanded - Whether the file is expanded
     * @param {Object} currentFilters - Current filter state
     * @param {string} sortBy - Sort order for findings
     * @returns {string} HTML for the file group
     */
    fileGroup(filePath, fileFindings, isExpanded, currentFilters, sortBy) {
        // Strip job ID prefix from filename (format: uuid_filename.ext)
        // UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (8-4-4-4-12 hex digits)
        // Only match actual UUIDs, not arbitrary hex sequences
        const rawFileName = filePath.split(/[/\\]/).pop() || filePath;
        const fileName = rawFileName.replace(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/, '');
        const severityCounts = getSeverityCounts(fileFindings);
        
        return `
            <div class="file-group">
                <div class="file-header" data-file-path="${filePath.replace(/"/g, '&quot;')}">
                    <div class="file-header-left">
                        ${isExpanded ? '▼' : '▶'}
                        📄
                        <div class="file-info">
                            <span class="file-name">${fileName}</span>
                        </div>
                    </div>
                    <div class="file-header-right">
                        ${currentFilters.severity === 'all' ? `
                            <div class="file-count-badge">
                                ${fileFindings.length} issue${fileFindings.length !== 1 ? 's' : ''}
                            </div>
                        ` : ''}
                        <div class="severity-badges">
                            ${getOrderedSeverityEntries(severityCounts).map(([severity, count]) => {
                                // Only show severity badges when severity filter is 'all' or matches this severity
                                if (currentFilters.severity === 'all' || currentFilters.severity === severity) {
                                    return `
                                        <span class="severity-count-badge ${severity.toLowerCase()}">
                                            ${count} ${severity.toLowerCase()}
                                        </span>
                                    `;
                                }
                                return '';
                            }).join('')}
                        </div>
                    </div>
                </div>
                
                ${isExpanded ? `
                    <div class="file-findings">
                        ${sortFindingsInGroup(fileFindings, sortBy).map((finding, index) => 
                            this.findingItem(finding)
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    },

    /**
     * Generates HTML for a single finding item
     * @param {Object} finding - The finding object
     * @returns {string} HTML for the finding item
     */
    findingItem(finding) {
        return `
            <div class="finding ${finding.severity.toLowerCase()}">
                <div class="finding-header">
                    ${getSeverityIcon(finding.severity)}
                    <strong>[<a class="finding-rule-link" data-rule="${finding.rule_id}" role="button" tabindex="0" title="Open Grimoire entry for ${finding.rule_id}">${finding.rule_id}</a>]</strong> ${finding.message}
                </div>
                <div class="finding-details">
                    <span><strong>Line:</strong> ${finding.line}</span>
                </div>
            </div>
        `;
    },

    /**
     * Generates HTML for the "no issues" message
     * @returns {string} HTML for the no issues message
     */
    noIssues() {
        return `
            <div class="no-issues">
                ✅ <strong>No issues found!</strong> Your code is magical!
            </div>
        `;
    },

    /**
     * Generates HTML for the context panel
     * @param {Object} contextData - The context data object
     * @param {boolean} isComplete - Whether the analysis is complete
     * @param {Object} currentResult - The current result object (for config info)
     * @returns {string} HTML for the context panel
     */
    contextPanel(contextData, isComplete, currentResult) {
        if (!contextData) return '';
        
        let html = '';
        
        // Files examined (magical terminology)
        if (contextData.files_analyzed && contextData.files_analyzed.length > 0) {
            html += `
                <div class="context-files">
                    <h4>✅ Files Examined (${contextData.files_analyzed.length})</h4>
                    <div class="context-files-list">
                        ${contextData.files_analyzed.map(file => {
                            // Remove job ID prefix if present (format: uuid_filename.ext)
                            const cleanFileName = file.replace(/^[a-f0-9-]+_/, '');
                            const extension = cleanFileName.split('.').pop().toUpperCase();
                            const icon = extension === 'PMD' ? '📄' : 
                                       extension === 'SMD' ? '⚙️' : 
                                       extension === 'AMD' ? '🏗️' : 
                                       extension === 'POD' ? '🎨' : 
                                       extension === 'SCRIPT' ? '📜' : '📄';
                            return `
                                <div class="context-file-item">
                                    <span class="file-icon">${icon}</span>
                                    <span class="file-name">${cleanFileName}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // Configuration used
        if (currentResult && currentResult.config_name) {
            const configSource = currentResult.config_source || 'presets';
            const isBuiltIn = configSource === 'presets';
            
            // Only show path for non-built-in configs
            const configDisplay = isBuiltIn ? 
                currentResult.config_name.split(/[/\\]/).pop().replace('.json', '') : 
                currentResult.config_name;
            
            html += `
                <div class="context-config">
                    <h4>⚙️ Configuration Used</h4>
                    <div class="context-config-item">
                        <span class="config-icon">🔧</span>
                        <span class="config-name">${configDisplay}</span>
                    </div>
                </div>
            `;
        }
        
        // Missing files (renamed and restructured)
        if (contextData.files_missing && contextData.files_missing.length > 0) {
            // Only show AMD and SMD as "needed for full validation"
            const requiredFiles = contextData.files_missing.filter(type => ['AMD', 'SMD'].includes(type));
            
            if (requiredFiles.length > 0) {
                html += `
                    <div class="context-missing">
                        <h4>⚠️ Missing Artifacts</h4>
                        <div class="context-missing-items">
                `;
                
                // Show only required files
                requiredFiles.forEach(type => {
                    html += `<span class="context-missing-item required">${type}</span>`;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // Impact analysis (rules not executed)
        if (contextData.impact && contextData.impact.rules_not_executed && contextData.impact.rules_not_executed.length > 0) {
            html += `
                <div class="context-impact">
                    <h4>📜 Rules Not Invoked</h4>
                    <p class="context-impact-subtitle">Some validations could not be cast due to missing components.</p>
                    <div class="context-impact-list">
                        ${contextData.impact.rules_not_executed.map(rule => `
                            <div class="context-impact-item">
                                <strong>🚫 ${rule.rule}</strong>
                                <span>Skipped — missing required ${rule.reason.toLowerCase().replace('requires ', '').replace(' file', '')} file.</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Impact analysis (rules partially executed)
        if (contextData.impact && contextData.impact.rules_partially_executed && contextData.impact.rules_partially_executed.length > 0) {
            html += `
                <div class="context-impact context-impact-partial">
                    <h4>⚠️ Rules Partially Invoked</h4>
                    <p class="context-impact-subtitle">Some validations were partially cast due to missing components.</p>
                    <div class="context-impact-list">
                        ${contextData.impact.rules_partially_executed.map(rule => `
                            <div class="context-impact-item">
                                <strong>⚠️ ${rule.rule}</strong>
                                <span>Skipped: ${rule.skipped_checks ? rule.skipped_checks.join(', ') : 'unknown checks'} — ${rule.reason.toLowerCase()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Tip (magical guidance)
        if (!isComplete) {
            const requiredFiles = (contextData.files_missing || []).filter(type => ['AMD', 'SMD'].includes(type));
            
            let tipText = '';
            if (requiredFiles.length > 0) {
                tipText = `Add these components to complete the circle: ${requiredFiles.join(' and ')}.`;
            } else {
                tipText = 'Add missing components to complete the divination.';
            }
            
            html += `
                <div class="context-tip">
                    <p>💡 <strong>Tip:</strong> ${tipText}</p>
                </div>
            `;
        }
        
        return html;
    }
};

