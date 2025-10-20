// Results display and filtering for Arcane Auditor web interface

import { 
    getSeverityIcon, 
    getSeverityCounts, 
    getOrderedSeverityEntries,
    getFileTypeFromPath,
    groupFindingsByFile,
    sortFindingsInGroup,
    sortFileGroups,
    getLastSortBy,
    getLastSortFilesBy,
    saveSortBy,
    saveSortFilesBy
} from './utils.js';

export class ResultsRenderer {
    constructor(app) {
        this.app = app;
        this.contextPanelExpanded = false;
    }

    renderResults() {
        this.renderSummary();
        this.renderFilters();
        this.renderFindings();
    }

    renderSummary() {
        const summary = document.getElementById('summary');
        const result = this.app.currentResult;
        
        const severityCounts = getSeverityCounts(result.findings);

        summary.innerHTML = `
            <h4>📈 Summary</h4>
            ${this.app.uploadedFileName ? `
                <div class="summary-filename-section">
                    <div class="summary-filename">📁 ${this.app.uploadedFileName}</div>
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
    }

    renderFilters() {
        // Filters are now rendered inline with findings, so this method is no longer needed
        // The filters are rendered directly in renderFindings()
        return;
    }

    renderFindings() {
        const findings = document.getElementById('findings');
        
        if (this.app.filteredFindings.length === 0) {
            findings.innerHTML = `
                <div class="no-issues">
                    ✅ <strong>No issues found!</strong> Your code is magical!
                </div>
            `;
            return;
        }

        const groupedFindings = groupFindingsByFile(this.app.filteredFindings);
        const sortedGroupedFindings = sortFileGroups(groupedFindings, this.app.currentFilters.sortFilesBy);
        
        findings.innerHTML = `
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
                            <option value="alphabetical" ${this.app.currentFilters.sortFilesBy === 'alphabetical' ? 'selected' : ''}>File Name</option>
                            <option value="issue-count" ${this.app.currentFilters.sortFilesBy === 'issue-count' ? 'selected' : ''}>Issue Count</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">Issue Order</div>
                        <select id="sort-by" onchange="app.updateSortBy(this.value)">
                            <option value="severity" ${this.app.currentFilters.sortBy === 'severity' ? 'selected' : ''}>Severity</option>
                            <option value="line" ${this.app.currentFilters.sortBy === 'line' ? 'selected' : ''}>Line Number</option>
                            <option value="rule" ${this.app.currentFilters.sortBy === 'rule' ? 'selected' : ''}>Rule ID</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="findings-content">
                ${Object.entries(sortedGroupedFindings).map(([filePath, fileFindings]) => {
                    const isExpanded = this.app.expandedFiles.has(filePath);
                    // Strip job ID prefix from filename (format: uuid_filename.ext)
                    const rawFileName = filePath.split(/[/\\]/).pop() || filePath;
                    const fileName = rawFileName.replace(/^[a-f0-9-]+_/, '');
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
                                    ${this.app.currentFilters.severity === 'all' ? `
                                        <div class="file-count-badge">
                                            ${fileFindings.length} issue${fileFindings.length !== 1 ? 's' : ''}
                                        </div>
                                    ` : ''}
                                    <div class="severity-badges">
                                        ${getOrderedSeverityEntries(severityCounts).map(([severity, count]) => {
                                            // Only show severity badges when severity filter is 'all' or matches this severity
                                            if (this.app.currentFilters.severity === 'all' || this.app.currentFilters.severity === severity) {
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
                                    ${sortFindingsInGroup(fileFindings, this.app.currentFilters.sortBy).map((finding, index) => `
                                        <div class="finding ${finding.severity.toLowerCase()}">
                                            <div class="finding-header">
                                                ${getSeverityIcon(finding.severity)}
                                                <strong>[${finding.rule_id}]</strong> ${finding.message}
                                            </div>
                                            <div class="finding-details">
                                                <span><strong>Line:</strong> ${finding.line}</span>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        // Update filter options after HTML is rendered
        this.updateFilterOptions();
    }

    // Filter and sort methods
    updateSeverityFilter(severity) {
        this.app.currentFilters.severity = severity;
        this.updateFilterOptions();
        this.applyFilters();
    }

    updateFileTypeFilter(fileType) {
        this.app.currentFilters.fileType = fileType;
        this.updateFilterOptions();
        this.applyFilters();
    }

    updateSortBy(sortBy) {
        this.app.currentFilters.sortBy = sortBy;
        saveSortBy(sortBy);
        this.renderFindings();
    }

    updateSortFilesBy(sortFilesBy) {
        this.app.currentFilters.sortFilesBy = sortFilesBy;
        saveSortFilesBy(sortFilesBy);
        this.renderFindings();
    }

    updateFilterOptions() {
        // Get all available severities and file types from current findings
        const availableSeverities = new Set(['all']);
        const availableFileTypes = new Set(['all']);
        
        this.app.currentResult.findings.forEach(finding => {
            availableSeverities.add(finding.severity);
            availableFileTypes.add(getFileTypeFromPath(finding.file_path));
        });

        // Update severity filter options
        const severitySelect = document.getElementById('severity-filter');
        if (severitySelect) {
            const currentSeverity = this.app.currentFilters.severity;
            const currentFileType = this.app.currentFilters.fileType;
            
            // If file type is selected, only show severities that exist for that file type
            let filteredSeverities = availableSeverities;
            if (currentFileType !== 'all') {
                filteredSeverities = new Set(['all']);
                this.app.currentResult.findings.forEach(finding => {
                    if (getFileTypeFromPath(finding.file_path) === currentFileType) {
                        filteredSeverities.add(finding.severity);
                    }
                });
            }
            
            // Update options
            severitySelect.innerHTML = '';
            
            // Sort with 'all' first, then alphabetically
            const sortedSeverities = Array.from(filteredSeverities).sort((a, b) => {
                if (a === 'all') return -1;
                if (b === 'all') return 1;
                return a.localeCompare(b);
            });
            
            sortedSeverities.forEach(severity => {
                const option = document.createElement('option');
                option.value = severity;
                
                // Calculate count for this severity
                let count = 0;
                if (severity === 'all') {
                    count = this.app.currentResult.findings.length;
                } else {
                    count = this.app.currentResult.findings.filter(finding => {
                        const severityMatch = finding.severity === severity;
                        const fileTypeMatch = currentFileType === 'all' || getFileTypeFromPath(finding.file_path) === currentFileType;
                        return severityMatch && fileTypeMatch;
                    }).length;
                }
                
                option.textContent = severity === 'all' ? `All Severities (${count})` : `${severity} (${count})`;
                if (severity === currentSeverity) {
                    option.selected = true;
                }
                severitySelect.appendChild(option);
            });
            
            // If current severity is not available, reset to 'all'
            if (!filteredSeverities.has(currentSeverity)) {
                this.app.currentFilters.severity = 'all';
                severitySelect.value = 'all';
            }
        }

        // Update file type filter options
        const fileTypeSelect = document.getElementById('file-type-filter');
        if (fileTypeSelect) {
            const currentFileType = this.app.currentFilters.fileType;
            const currentSeverity = this.app.currentFilters.severity;
            
            // If severity is selected, only show file types that have that severity
            let filteredFileTypes = availableFileTypes;
            if (currentSeverity !== 'all') {
                filteredFileTypes = new Set(['all']);
                this.app.currentResult.findings.forEach(finding => {
                    if (finding.severity === currentSeverity) {
                        filteredFileTypes.add(getFileTypeFromPath(finding.file_path));
                    }
                });
            }
            
            // Update options
            fileTypeSelect.innerHTML = '';
            
            // Sort with 'all' first, then alphabetically
            const sortedFileTypes = Array.from(filteredFileTypes).sort((a, b) => {
                if (a === 'all') return -1;
                if (b === 'all') return 1;
                return a.localeCompare(b);
            });
            
            sortedFileTypes.forEach(fileType => {
                const option = document.createElement('option');
                option.value = fileType;
                
                // Calculate count for this file type
                let count = 0;
                if (fileType === 'all') {
                    count = this.app.currentResult.findings.length;
                } else {
                    count = this.app.currentResult.findings.filter(finding => {
                        const fileTypeMatch = getFileTypeFromPath(finding.file_path) === fileType;
                        const severityMatch = currentSeverity === 'all' || finding.severity === currentSeverity;
                        return fileTypeMatch && severityMatch;
                    }).length;
                }
                
                option.textContent = fileType === 'all' ? `All File Types (${count})` : `${fileType} (${count})`;
                if (fileType === currentFileType) {
                    option.selected = true;
                }
                fileTypeSelect.appendChild(option);
            });
            
            // If current file type is not available, reset to 'all'
            if (!filteredFileTypes.has(currentFileType)) {
                this.app.currentFilters.fileType = 'all';
                fileTypeSelect.value = 'all';
            }
        }
    }

    applyFilters() {
        this.app.filteredFindings = this.app.currentResult.findings.filter(finding => {
            const severityMatch = this.app.currentFilters.severity === 'all' || finding.severity === this.app.currentFilters.severity;
            const fileTypeMatch = this.app.currentFilters.fileType === 'all' || getFileTypeFromPath(finding.file_path) === this.app.currentFilters.fileType;
            return severityMatch && fileTypeMatch;
        });
        this.renderFindings();
    }

    // File expansion methods
    expandAllFiles() {
        const fileHeaders = document.querySelectorAll('.file-header');
        fileHeaders.forEach(header => {
            const filePath = header.dataset.filePath;
            this.app.expandedFiles.add(filePath);
        });
        this.renderFindings();
    }

    collapseAllFiles() {
        this.app.expandedFiles.clear();
        this.renderFindings();
    }

    toggleFileExpansion(filePath) {
        if (this.app.expandedFiles.has(filePath)) {
            this.app.expandedFiles.delete(filePath);
        } else {
            this.app.expandedFiles.add(filePath);
        }
        this.renderFindings();
    }

    // Context panel methods
    displayContext(contextData) {
        if (!contextData) return;
        
        const contextSection = document.getElementById('context-section');
        const contextContent = document.getElementById('context-content');
        const contextIcon = document.getElementById('context-icon');
        const contextTitleText = document.getElementById('context-title-text');
        
        // Determine if analysis is complete or partial
        const isComplete = contextData.context_status === 'complete';
        
        // Update icon and title with magical flair
        if (isComplete) {
            contextIcon.textContent = '✨';
            contextTitleText.textContent = 'Evaluation ✦';
        } else {
            contextIcon.textContent = '🌙';
            contextTitleText.textContent = 'Divination Incomplete';
        }
        
        // Add status badge to the header
        const contextHeader = document.querySelector('.context-header');
        if (contextHeader) {
            // Remove any existing status badge
            const existingBadge = contextHeader.querySelector('.context-header-badge');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            // Determine badge text based on context
            let badgeText = '';
            if (isComplete) {
                badgeText = '✅ Complete';
            } else {
                // Check if any rules were skipped
                const hasSkippedRules = contextData.impact && 
                    ((contextData.impact.rules_not_executed && contextData.impact.rules_not_executed.length > 0) ||
                     (contextData.impact.rules_partially_executed && contextData.impact.rules_partially_executed.length > 0));
                
                if (hasSkippedRules) {
                    badgeText = '⚠️ Partial';
                } else {
                    badgeText = '⚠️ Partial';
                }
            }
            
            // Add new status badge
            const statusBadge = document.createElement('div');
            statusBadge.className = `context-header-badge ${isComplete ? 'complete' : 'partial'}`;
            statusBadge.textContent = badgeText;
            contextHeader.appendChild(statusBadge);
        }
        
        // Build context content HTML
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
        if (this.app.currentResult && this.app.currentResult.config_name) {
            html += `
                <div class="context-config">
                    <h4>⚙️ Configuration Used</h4>
                    <div class="context-config-item">
                        <span class="config-icon">🔧</span>
                        <span class="config-name">${this.app.currentResult.config_name}</span>
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
        
        contextContent.innerHTML = html;
        contextSection.style.display = 'block';
        
        // Set initial collapsed state
        this.contextPanelExpanded = false;
        const contextToggle = document.getElementById('context-toggle');
        if (contextToggle) {
            contextToggle.classList.remove('expanded');
        }
    }

    toggleContextPanel() {
        const contextContent = document.getElementById('context-content');
        const contextToggle = document.getElementById('context-toggle');
        
        this.contextPanelExpanded = !this.contextPanelExpanded;
        
        if (this.contextPanelExpanded) {
            contextContent.classList.remove('collapsed');
            contextToggle.classList.add('expanded');
        } else {
            contextContent.classList.add('collapsed');
            contextToggle.classList.remove('expanded');
        }
    }

    // Reset method
    resetForNewUpload() {
        this.filteredFindings = [];
        this.expandedFiles.clear();
        this.contextPanelExpanded = false;
        this.currentFilters = {
            severity: 'all',
            fileType: 'all',
            sortBy: getLastSortBy(),
            sortFilesBy: getLastSortFilesBy()
        };
    }
}
