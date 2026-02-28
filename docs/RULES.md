# Arcane Auditor Rules Grimoire 📜

*Ancient wisdom distilled into 42 mystical validation rules*

This grimoire provides a comprehensive overview of all **42 validation rules** wielded by the Arcane Auditor. These enchantments help reveal hidden code quality issues, style violations, and structural problems that compilers don't detect but are essential for master code wizards to identify.

## 📋 Table of Contents

### Script Rules

- [ScriptArrayMethodUsageRule](#scriptarraymethodusagerule)
- [ScriptComplexityRule](#scriptcomplexityrule)
- [ScriptNestedArraySearchRule](#scriptnestedarraysearchrule)
- [ScriptConsoleLogRule](#scriptconsolelogrule)
- [ScriptDeadCodeRule](#scriptdeadcoderule)
- [ScriptDescriptiveParameterRule](#scriptdescriptiveparameterrule)
- [ScriptEmptyFunctionRule](#scriptemptyfunctionrule)
- [ScriptFunctionParameterCountRule](#scriptfunctionparametercountrule)
- [ScriptFunctionParameterNamingRule](#scriptfunctionparameternamingrule)
- [ScriptFunctionReturnConsistencyRule](#scriptfunctionreturnconsistencyrule)
- [ScriptLongBlockRule](#scriptlongblockrule)
- [ScriptLongFunctionRule](#scriptlongfunctionrule)
- [ScriptMagicNumberRule](#scriptmagicnumberrule)
- [ScriptNestingLevelRule](#scriptnestinglevelrule)
- [ScriptOnSendSelfDataRule](#scriptonsendselfdatarule)
- [ScriptStringConcatRule](#scriptstringconcatrule)
- [ScriptUnusedFunctionParametersRule](#scriptunusedfunctionparametersrule)
- [ScriptUnusedFunctionRule](#scriptunusedfunctionrule)
- [ScriptUnusedIncludesRule](#scriptUnusedIncludesRule)
- [ScriptUnusedVariableRule](#scriptunusedvariablerule)
- [ScriptVarUsageRule](#scriptvarusagerule)
- [ScriptVariableNamingRule](#scriptvariablenamingrule)
- [ScriptVerboseBooleanCheckRule](#scriptverbosebooleancheckrule)

### Structure Rules

- [HardcodedWorkdayAPIRule](#Hardcodedworkdayapirule)
- [EmbeddedImagesRule](#embeddedimagesrule)
- [EndpointBaseUrlTypeRule](#endpointbaseurltyperule)
- [EndpointFailOnStatusCodesRule](#endpointfailonstatuscodesrule)
- [EndpointNameLowerCamelCaseRule](#endpointnamelowercamelcaserule)
- [FileNameLowerCamelCaseRule](#filenamelowercamelcaserule)
- [FooterPodRequiredRule](#footerpodrequiredrule)
- [GridPagingWithSortableFilterableRule](#gridpagingwithsortablefilterablerule)
- [HardcodedApplicationIdRule](#Hardcodedapplicationidrule)
- [HardcodedWidRule](#Hardcodedwidrule)
- [MultipleStringInterpolatorsRule](#multiplestringinterpolatorsrule)
- [NoIsCollectionOnEndpointsRule](#noiscollectiononendpointsrule)
- [NoPMDSessionVariablesRule](#nopmdsessionvariablesrule)
- [OnlyMaximumEffortRule](#onlymaximumeffortrule)
- [PMDSectionOrderingRule](#pmdsectionorderingrule)
- [PMDSecurityDomainRule](#pmdsecuritydomainrule)
- [OrchestrationSecurityDomainRule](#orchestrationsecuritydomainrule)
- [OrchestrationGlobalErrorHandlerRule](#orchestrationglobalerrorhandlerrule)
- [StringBooleanRule](#stringbooleanrule)
- [WidgetIdLowerCamelCaseRule](#widgetidlowercamelcaserule)
- [WidgetIdRequiredRule](#widgetidrequiredrule)

## Rule Categories

The rules are organized into two main categories:

- **Script Rules**: Code quality and best practices for PMD, Pod, and standalone script files
- **Structure Rules**: Widget configurations, endpoint validation, structural compliance, Hardcoded values, PMD organization, and orchestration (`.orchestration`, `.suborchestration`) validation

## Severity Levels

Rules use a simplified two-tier severity system:

- 🚨 **ACTION**: Issues that should be addressed immediately
- ℹ️ **ADVICE**: Recommendations for code quality and best practices

---

## 🪄 Script Rules

*The Script Rules form the incantations that shape the logic within your enchanted scrolls. These mystical validations ensure your code flows with the elegance and power befitting a master wizard.*

*These rules analyze PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files for comprehensive code quality validation.*

### ScriptVarUsageRule

**Severity:** ℹ️ADVICE
**Description:** Ensures scripts use 'let' or 'const' instead of 'var' (best practice)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

The `var` keyword has function scope, which can cause unexpected behavior and bugs when the same name is reused in nested blocks. Using `let` (block scope) and `const` (immutable) makes your code more predictable and prevents accidental variable shadowing issues.

Using the `const` keyword is also a good way to communicate `intent` to your readers.

**What it catches:**

- Usage of `var` declarations instead of modern `let`/`const`
- Variable declarations that don't follow Extend best practices

**Example violations:**

```javascript
var myVariable = "value";  // ❌ Should use 'let' or 'const'
```

**Fix:**

```javascript
const myVariable = "value";  // ✅ Use 'const' for immutable values
let myVariable = "value";    // ✅ Use 'let' for mutable values
```

---

### ScriptDeadCodeRule

**Severity:** ℹ️ADVICE
**Description:** Validates export patterns in standalone script files by detecting declared variables that are never exported or used
**Applies to:** Standalone .script files ONLY

**Why This Matters:**

Dead code in standalone script files increases your application's bundle size and memory footprint, making pages load slower. Every unused function or constant is still parsed and loaded, wasting resources. Removing dead code keeps your application lean and makes it easier for other developers to understand what's actually being used.

**What This Rule Does:**
This rule validates the export pattern specific to standalone `.script` files. Standalone script files use an export object literal at the end to expose functions and constants. This rule checks that ALL declared top-level variables (functions, strings, numbers, objects, etc.) are either:

1. Exported in the final object literal, OR
2. Used internally by other code in the file

**Intent:** Ensure standalone script files follow proper export patterns and don't contain unused declarations that increase bundle size.

**What it catches:**

- Top-level variables (of any type) declared but not exported AND not used internally
- Function-scoped variables that are declared but never used
- Dead code that increases bundle size unnecessarily

**Example violations:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };
const unusedHelper = function() { return "unused"; };    // ❌ Dead code - not exported or used
const apiUrl = "https://api.example.com";  // ❌ Dead code - constant not exported or used

{
  "getCurrentTime": getCurrentTime  // ❌ unusedHelper and API_KEY are dead code
}
```

**Fix:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };
const helperFunction = function() { return "helper"; };    // ✅ Will be exported
const apiUrl = "https://api.example.com";  // ✅ Will be exported

{
  "getCurrentTime": getCurrentTime,
  "helperFunction": helperFunction,
  "apiUrl": apiUrl  // ✅ All declarations are exported
}
```

**Example with internal usage:**

```javascript
// In util.script
const cacheTtl = 3600;  // ✅ Used internally (not exported)
const getCurrentTime = function() { 
  return { "time": date:now(), "ttl": cacheTtl };  // Uses cacheTtl
};

{
  "getCurrentTime": getCurrentTime  // ✅ cacheTtl is used internally
}
```

### ScriptNestingLevelRule

**Severity:** ℹ️ADVICE
**Description:** Ensures scripts don't have excessive nesting levels (*default* max 4 levels)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files
**Configurable:** ✅ Maximum nesting level can be customized

**Why This Matters:**

Deep nesting (more than 4 levels of if/for/while statements) makes code exponentially harder to read, test, and debug. Each nesting level adds cognitive load, making it difficult to track which conditions are active and increasing the likelihood of logic errors. Flattening nested code through early returns or extracted functions dramatically improves maintainability.

**What it catches:**

- Overly nested code structures (if statements, loops, functions)
- Code that's difficult to read and maintain due to deep nesting

**Configuration:**

The maximum nesting level can be customized in config files:

```json
{
  "ScriptNestingLevelRule": {
    "enabled": true,
    "custom_settings": {
      "max_nesting_level": 3
    }
  }
}
```

**Example violations:**

```javascript
function processData(data) {
    if (!empty data) { // Level 1
        if (data.isValid) { // Level 2
            if (data.hasContent) { // Level 3
                if (data.content.size() > 0) { // Level 4
                    if (data.content[0].isActive) { // Level 5 ❌ Too deep!
                        return data.content[0];
                    }
                }
            }
        }
    }
}
```

**Fix:**

```javascript
function processData(data) {
    if (empty data.content || !data.isValid || !data.hasContent) {
        return null;
    }

    return data.content[0].isActive ? data.content[0] : null;
}
```

---

### ScriptComplexityRule

**Severity:** ℹ️ADVICE
**Description:** Ensures scripts don't have excessive cyclomatic complexity (max 10)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Cyclomatic complexity measures the number of independent paths through your code (every *if*, *else*, *loop*, etc. adds to it). High complexity (>10) means your function has too many decision points, making it exponentially harder to test all scenarios and increasing the chance of bugs. Breaking complex functions into smaller, focused ones makes testing easier and reduces defects.

**What it catches:**

- Functions with too many decision points (*if*/*else*, *loops*, *ternary operators*, etc.)
- Complex functions that are hard to test and maintain
- Functions that likely need to be broken down
- Each top-level function is analyzed separately
- For pure procedural scripts (no functions), the entire script block is analyzed

> **🧙‍♂️ Wizard's Note:** This rule currently evaluates **either** individual functions **or** procedural script blocks, but not both mixed together. If your script has inline function declarations, only those functions are checked; the procedural code between functions is not separately analyzed for complexity. This may be changed in a future update, but carries a high level of complexity (ironic, yes!)

**Example violations:**

```javascript
const processOrder = function(order) {
    // Function starts with score of 1 as base

    const highValueMin = 1000;
    const discountMin = 500;
    const vipYearMin = 5

    // Decision point +1: if
    if (order.type == 'premium') {
        // Decision point +1: if
        if (order.amount > highValueMin) {
            // Decision point +1: if
            if (order.customer.vip) {
                // Decision point +1: if
                if (order.customer.loyaltyYears > vipYearMin) {
                    applyVIPDiscount();
                }
            }
            // Decision point +1: if
            if (order.shippingAddress.country == 'US') {
                applyDomesticShipping();
            }
        // Decision point +1: else if
        } else if (order.amount > discountMin) {
            applyStandardDiscount();
        }
    // Decision point +1: else if
    } else if (order.type == 'standard') {
        // Decision point +1: for
        for (var i = 0; i < order.items.length; i++) {
            // Decision point +1: if
            if (order.items[i].category == 'electronics') {
                // Decision point +1: if
                if (order.items[i].warrantyRequired) {
                    addWarranty(order.items[i]);
                }
            // Decision point +1: else if (EXCEEDS THRESHOLD)
            } else if (order.items[i].category == 'clothing') {
                applyClothingTax();
            }
        }
    }
    // Cyclomatic Complexity: 12 (exceeds default threshold of 10)
}
```

**Fix:**

Break the function into smaller, focused functions:
```javascript
const processOrder = function(order) {
    if (order.type == 'premium') {
        processPremiumOrder(order);
    } else if (order.type == 'standard') {
        processStandardOrder(order);
    }
    // Complexity: 3 ✅
}

const processPremiumOrder = function(order) {
    const highValueMin = 1000;
    const discountMin = 500;

    if (order.amount > maxAmount) {
        processHighValueOrder(order);
    } else if (order.amount > discountMin) {
        applyStandardDiscount();
    }
    // Complexity: 3 ✅
}

const processHighValueOrder = function(order) {
    if (order.customer.vip && order.customer.loyaltyYears > 5) {
        applyVIPDiscount();
    }
    if (order.shippingAddress.country == 'US') {
        applyDomesticShipping();
    }
    // Complexity: 4 ✅
}

const processStandardOrder = function(order) {
    order.items.forEach(item => {
      processOrderItem(item);
    })
    // Complexity: 1 ✅
}

const processOrderItem = function(item) {
    if (item.category == 'electronics' && item.warrantyRequired) {
        addWarranty(item);
    } else if (item.category == 'clothing') {
        applyClothingTax();
    }
    // Complexity: 4 ✅
}
```
> **🧙‍♂️ Wizard's Note:** Complexity thresholds will be configurable in a future release.*

---

### ScriptLongFunctionRule

**Severity:** ℹ️ADVICE
**Description:** Ensures scripts don't have excessively long functions (default max 50 lines)
**Applies to:** PMD *scripts* section and standalone .script files (handles all function definitions)

**Why This Matters:**

Functions longer than 50 lines typically violate the single responsibility principle - they're doing too many things. Long functions are harder to understand, test, and reuse, and they often hide bugs in the complexity. Breaking them into smaller, focused functions with clear names makes code self-documenting and easier to maintain.

**What it catches:**

- Functions that exceed 50 lines of code
- Monolithic functions that should be broken down
- Functions that likely violate single responsibility principle
- **Note:** Nested functions are analyzed independently - but inner function lines are also included in outer function counts. This means you could get multiple violations when an inner function exceeds the threshold. This means the outer function does, too!

**Configuration Options:**

- `skip_comments` (boolean, default: false): When true, comment lines are excluded from line count. When false (default), lines with comments are counted.
- `skip_blank_lines` (boolean, default: false): When true, blank/empty lines are excluded from line count. When false (default), blank lines are counted.
- `max_lines` (integer, default: 50): Maximum allowed lines per function

**Example violations:**

```pmd
const processLargeDataset = function(data) {
    // ... 60 lines of code ...
    // This function is doing too many things
};
```

**Fix:**

```pmd
const processLargeDataset = function(data) {
    const validated = validateData(data);
    const processed = transformData(validated);
    return formatOutput(processed);
};

const validateData = function(data) {
    // ... validation logic ...
};

const transformData = function(data) {
    // ... transformation logic ...
};

const formatOutput = function(data) {
    // ... formatting logic ...
};
```

**Configuration:**

The threshold can be customized in config files:

```json
{
  "rules": {
    "ScriptLongFunctionRule": {
      "enabled": true,
      "custom_settings": {
        "max_lines": 50,
        "skip_comments": false,
        "skip_blank_lines": false
      }
    }
  }
}
```

---

### ScriptLongBlockRule

**Severity:** ℹ️ADVICE
**Description:** Ensures embedded script blocks in PMD/POD files don't exceed maximum line count (*default* max 30 lines). Skips the `script` field entirely (handled by ScriptLongFunctionRule) and counts ALL lines in embedded blocks including inline functions and callbacks.
**Applies to:** PMD embedded scripts and Pod endpoint/widget scripts only. Standalone .script files are excluded (handled by ScriptLongFunctionRule instead).

**Why This Matters:**

Embedded script blocks (in event handlers like onLoad, onChange, onSend, or widget properties) should be kept small and focused. When these blocks grow beyond 30 lines, they become difficult to read, test, and maintain. Long embedded blocks often contain complex logic that should be extracted into reusable functions in the `script` section (or `.script` files in the case of functionality that could be shared across pages).

This rule enforces the principle that embedded blocks should contain only simple, focused logic while complex operations belong in dedicated functions.

**What it catches:**

- Script blocks in PMD/POD embedded fields (onLoad, onChange, onSend, widget properties, etc.) that exceed 30 lines
- Embedded blocks containing inline functions, callbacks, and procedural code that should be refactored
- Script blocks that violate single responsibility principle by doing too much in one place
- **Note:** The `script` field in PMD files and standalone `.script` files are excluded entirely as they're handled by [ScriptLongFunctionRule](#scriptlongfunctionrule)

**Configuration Options:**

- `skip_comments` (boolean, default: false): When true, comment lines are excluded from line count. When false (default), all lines including comments are counted.
- `skip_blank_lines` (boolean, default: false): When true, blank/empty lines are excluded from line count. When false (default), all lines including blank lines are counted.
- `max_lines` (integer, default: 30): Maximum allowed lines per script block

**Example violations:**

```pmd
// In onLoad field
<%
    const workerData = getWorkerData();
    const processedData = processWorkerData(workerData);
    const validationResults = validateWorkerData(processedData);
    const formattedData = formatWorkerData(validationResults);
    const enrichedData = enrichWorkerData(formattedData);
    const finalData = applyBusinessRules(enrichedData);
    const displayData = prepareDisplayData(finalData);
    const summaryData = generateSummary(displayData);
    const reportData = createReport(summaryData);
    const exportData = prepareExport(reportData);
    const notificationData = prepareNotifications(exportData);
    const auditData = createAuditTrail(notificationData);
    const cacheData = prepareCache(auditData);
    const responseData = formatResponse(cacheData);
    // ... 20+ more lines of data processing ...
    pageVariables.workerData = responseData;
%>
```

**Fix:**

```pmd
// Break into focused functions
<%
    const workerData = getWorkerData();
    const processedData = processWorkerData(workerData);
    pageVariables.workerData = processedData;
%>

// Define functions in script section
const processWorkerData = function(rawData) {
    const validated = validateWorkerData(rawData);
    const formatted = formatWorkerData(validated);
    const enriched = enrichWorkerData(formatted);
    return enriched;
};

const validateWorkerData = function(data) {
    // ... focused validation logic
    return data;
};

const formatWorkerData = function(data) {
    // ... focused formatting logic
    return data;
};
```

**Configuration:**

The threshold can be customized in config files:

```json
{
  "rules": {
    "ScriptLongBlockRule": {
      "enabled": true,
      "custom_settings": {
        "max_lines": 30,
        "skip_comments": false,
        "skip_blank_lines": false
      }
    }
  }
}
```

---

### ScriptFunctionParameterCountRule

**Severity:** ℹ️ADVICE
**Description:** Ensures functions don't have too many parameters (*default* max 4)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Functions with more than 4 parameters can lead to bugs when arguments are passed in the wrong order. Refactoring to use parameter objects or breaking into smaller functions makes your code clearer and less error-prone.

**What it catches:**

- Functions with more than 4 parameters
- Functions that likely need parameter objects or refactoring

**Example violations:**

```javascript
function createUser(name, email, phone, address, age, department) { // ❌ 6 parameters
    // ... function body
}
```

**Fix:**

```javascript
// Break into smaller functions
function createUser(personalInfo, contactInfo, workInfo) { // ✅ 3 logical groups
    // ... function body
}
```

---

### ScriptConsoleLogRule

**Severity:** 🚨ACTION
**Description:** Ensures scripts don't contain console log statements (for production code)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Console statements left in production code can expose sensitive data in production logs, which may be accessible to individuals who should not have access to that same data. They're debugging artifacts that should be removed before deployment. Accidentally shipping console logs can leak business logic, data structures, or user information.

**What it catches:**

- `console log` statements that should be removed before production
- Debug statements left in production code

**Example violations:**

```javascript
function processData(data) {
    console.debug("Processing data:", data); // ❌ Debug statement
    return data.map(item => item.value);
}
```

**Fix:**

```javascript
function processData(data) {
    // Comment out or remove
    // console.debug("Processing data:", data);
    return data.map(item => item.value);
}
```

> **🧙 Wizard's Note:** If your code uses an app attribute flag to enable/disable logging based on environments, you may think you don't need this rule. However, my recommendation would be to keep the rule in place and use it as a reminder to quickly verify any logging in place and ensure that those statements are implemented using your attribute flags. If a log entry slips in that didn't use it, this means your code may unintentionally write to production logs, leading to the kind of PII leakage that the rule is intended to help avoid!

---

### ScriptVariableNamingRule

**Severity:** ℹ️ADVICE
**Description:** Ensures variables follow lowerCamelCase naming convention
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Consistent naming conventions make code easier to read and reduce cognitive load when switching between files or team members' code. lowerCamelCase is the standard for variables. Consistency enables faster comprehension and fewer mistakes.

**What it catches:**

- Variables that don't follow lowerCamelCase naming (snake_case, PascalCase, etc.)
- Inconsistent naming conventions

**Example violations:**

```javascript
const user_name = "John";     // ❌ snake_case
const UserAge = 25;           // ❌ PascalCase
const user-email = "email";   // ❌ kebab-case
```

**Fix:**

```javascript
const userName = "John";      // ✅ lowerCamelCase
const userAge = 25;           // ✅ lowerCamelCase
const userEmail = "email";    // ✅ lowerCamelCase
```

---

### ScriptFunctionParameterNamingRule

**Severity:** ℹ️ADVICE
**Description:** Ensures function parameters follow lowerCamelCase naming convention
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Parameter names are the first thing developers see when calling your functions. Inconsistent naming (like snake_case parameters when everything else uses camelCase) forces mental translation and slows comprehension. Following the same convention for parameters as variables creates a seamless reading experience and makes function signatures immediately understandable.

**What it catches:**

- Function parameters that don't follow lowerCamelCase naming convention
- Parameters using snake_case, PascalCase, or other naming conventions
- Inconsistent parameter naming that affects code readability

**Example violations:**

```javascript
// ❌ Non-lowerCamelCase parameters
const validateUser = function(user_id, user_name, is_active) {
    return user_id && user_name && is_active;
};

const processData = function(data_source) {
    return data_source.map(item => item.process());
};
```

**Fix:**

```javascript
// ✅ lowerCamelCase parameters
const validateUser = function(userId, userName, isActive) {
    return userId && userName && isActive;
};

const processData = function(dataSource) {
    return dataSource.map(item => item.process());
};
```

---

### ScriptArrayMethodUsageRule

**Severity:** ℹ️ADVICE
**Description:** Recommends using array higher-order methods (map, filter, forEach) instead of manual loops
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Array methods like map, filter, and forEach are more concise, less error-prone (no off-by-one errors), and communicate intent better than manual for-loops. They're also harder to get wrong since you don't manage the loop index yourself. Modern array methods make code more readable and reduce bugs related to loop boundaries or index manipulation.

**What it catches:**

- Traditional for loops that could be replaced with array higher-order methods
- Code that's more verbose than necessary

**Example violations:**

```javascript
const results = [];
for (let i = 0; i < items.length; i++) {  // ❌ Manual loop
    if (items[i].active) {
        results.add(items[i].name);
    }
}
```

**Fix:**

```javascript
const results = items
    .filter(item => item.active)     // ✅ Array higher-order methods
    .map(item => item.name);
```

---

### ScriptNestedArraySearchRule

**Severity:** ℹ️ADVICE
**Description:** Detects nested array search patterns that cause severe performance issues
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Nested array searches (like `workers.map(worker => orgData.find(org => org.id == worker.orgId))`) create O(n²) performance problems that can cause out-of-memory issues with large datasets. For every item in the outer array, the inner array is searched completely, leading to exponential performance degradation. This pattern is especially problematic in Workday Extend where data arrays can contain thousands of records.

**What it catches:**

- Nested array searches using `find()` or `filter()` inside `map()`, `forEach()`, or `filter()` callbacks
- Performance anti-patterns that cause exponential time complexity
- Code that searches external arrays from within iteration callbacks

**What it allows:**

- Searching owned data (e.g., `worker.skills.find()` where `skills` belongs to the `worker` parameter)
- Direct array operations without nesting
- Using `list:toMap()` patterns for efficient lookups

**Example violations:**

```javascript
// ❌ Nested search - searches entire orgData for each worker
const result = workers.map(worker => 
    orgData.find(org => org.id == worker.orgId)
);

// ❌ Nested filter - filters entire teams array for each department
departments.forEach(department => {
    const team = teams.filter(team => team.deptId == department.id);
});
```

**Fix:**

```javascript
// ✅ Use list:toMap for efficient O(1) lookups
const orgById = list:toMap(orgData, 'id');
const result = workers.map(worker => orgById[worker.orgId]);

// ✅ Or use a single filter with proper indexing
const teamByDeptId = list:toMap(teams, 'deptId');
departments.forEach(department => {
    const team = teamByDeptId[department.id];
});
```

---

### ScriptMagicNumberRule

**Severity:** ℹ️ADVICE
**Description:** Ensures scripts don't contain magic numbers (use named constants)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Magic numbers (like `if (price > 1000)` or `return value * 0.15`) hide meaning and make code harder to maintain. When the number appears in multiple places, updating it requires finding every occurrence, risking missed updates. Named constants (`const premiumThreshold = 1000`) make the purpose clear and provide a single source of truth for values that might need to change.

**What it catches:**

- Numeric literals without clear meaning
- Hard-coded numbers that should be constants

**Example violations:**

```javascript
function calculateDiscount(price) {
    if (price > 1000) {        // ❌ Magic number
        return price * 0.15;   // ❌ Magic number
    }
    return price * 0.05;       // ❌ Magic number
}
```

**Fix:**

```javascript
const premiumThreshold = 1000;
const premiumDiscount = 0.15;
const standardDiscount = 0.05;

function calculateDiscount(price) {
    if (price > premiumThreshold) {
        return price * premiumDiscount;
    }
    return price * standardDiscount;
}
```

---

### ScriptDescriptiveParameterRule

**Severity:** ℹ️ADVICE
**Description:** Ensures array method parameters use descriptive names instead of single letters (except 'a','b' for sorting methods, which is a globally excepted rule across programming languages)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Single-letter parameters in array methods (`x => x.active`) hide information about what is being processed, making code harder to scan and understand at a glance. Descriptive names (`user => user.active`) self-document the code and prevent confusion in nested method chains where multiple single-letter variables could refer to different things.

**What it catches:**

- Single-letter parameters in array methods that make code hard to read
- Nested array methods with confusing parameter names
- Non-descriptive variable names in map, filter, find, forEach, reduce, sort

**Configuration Options:**
- `allowed_single_letters` (array, default: []): Additional single-letter parameter names to allow beyond the built-in exceptions ('a', 'b' for sort)

**Example violations:**

```javascript
// ❌ Confusing single-letter parameters
const activeUsers = users.filter(x => x.active);
const userNames = users.map(u => u.name);
```

**Fix:**

```javascript
// ✅ Descriptive parameter names
const activeUsers = users.filter(user => user.active);
const userNames = users.map(user => user.name);

// ✅ Clear chained array methods
const result = departments
    .map(dept => dept.teams)
    .filter(team => team.active);

// ✅ Descriptive reduce parameters
const total = numbers.reduce((acc, num) => {acc + num});
```

**Special Cases:**

- **Sort methods:** `a`, `b` are allowed for comparison parameters
- **Reduce methods:** Suggests `acc` for accumulator, contextual names for items
- **Minimally context-aware:** Suggests `user` for `users.map()`, `team` for `teams.filter()`, etc.

**Configuration:**

```json
{
  "ScriptDescriptiveParameterRule": {
    "enabled": true,
    "severity_override": "ACTION",
    "custom_settings": {
      "allowed_single_letters": []
    }
  }
}
```

---

### ScriptFunctionReturnConsistencyRule

**Severity:** ℹ️ADVICE
**Description:** Ensures functions have consistent return patterns and handles guard clause patterns correctly
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Functions with inconsistent returns (some code paths return a value, others return nothing) cause subtle bugs where callers receive `null` unexpectedly. This leads to null reference errors downstream or incorrect conditional logic. Ensuring all code paths explicitly return (even if explicitly `null`) makes function behavior predictable and prevents runtime errors. This rule also recognizes valid guard clause patterns where early returns handle error conditions while the main logic continues.

**What it catches:**

- Functions with missing return statements ("not all code paths return")
- Inconsistent return patterns within functions ("inconsistent return pattern")
- Unreachable code after return statements ("unreachable code")
- **Note:** Nested functions are analyzed independently - each function's return consistency is evaluated separately
- **Guard clause patterns are recognized as valid** - when `else` branches return early for error handling while `if` branches continue with main logic

**Example violations:**

```pmd
// Missing return statement
const processUser = function(user) {
    if (user.active) {
        return user.name;
    }
    // ❌ Missing return statement
};

// Inconsistent return pattern
const calculateDiscount = function(price) {
    if (price > 1000) {
        return price * 0.15;  // Returns value
    } else {
        console.log("Standard price");  // ❌ No return
    }
    return price * 0.05;  // Final return
};

// Unreachable code
const getValue = function(data) {
    if (empty data) {
        return null;
    }
    return data.value;
    console.log("This never executes");  // ❌ Unreachable
};
```

**Valid patterns:**

```pmd
// Guard clause pattern (✅ Valid)
const processData = function(data) {
    if (empty data) {
        return null;  // Early return for error
    }
  
    // Main logic continues
    const processed = data.map(item => item.value);
    return processed;  // Final return
};

// Consistent returns (✅ Valid)
const processUser = function(user) {
    if (user.active) {
        return user.name;
    }
    return null;  // ✅ Explicit return
};

// Nested functions (✅ Each analyzed independently)
const outerFunction = function(data) {
    const innerFunction = function(item) {
        if (item.valid) {
            return item.value;
        }
        return null;  // Inner function's return consistency
    };
  
    return data.map(innerFunction);  // Outer function's return
};
```

---

### ScriptStringConcatRule

**Severity:** ℹ️ADVICE
**Description:** Recommends using PMD template syntax instead of string concatenation
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

String concatenation with `+` is verbose, error-prone (easy to forget spaces), and harder to read than template syntax. Workday Extend's template syntax (`{{variable}}`) is specifically designed for building strings with dynamic values, handles escaping automatically, and makes the intent clearer. Using the right tool prevents formatting bugs and improves readability.

**What it catches:**

- String concatenation using + operator
- Code that would be more readable with PMD template syntax

**Example violations:**

```javascript
const message = "Hello " + userName + ", welcome to " + appName; // ❌ String concatenation
```

**Fix:**

```javascript
const message = `Hello {{userName}}, welcome to {{appName}}`; // ✅ PMD template syntax
```

---

### ScriptVerboseBooleanCheckRule

**Severity:** ℹ️ADVICE
**Description:** Recommends using concise boolean expressions
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Verbose boolean checks like `if (isActive == true)` or `return (condition) ? true : false` add unnecessary noise and make code harder to scan. The value is already boolean, so the comparison is redundant. Concise expressions (`if (isActive)` or `return condition`) are clearer, more idiomatic, and reduce visual clutter.

**What it catches:**

- Verbose boolean comparisons that can be simplified
- Redundant boolean expressions

**Example violations:**

```javascript
if (user.active == true) { }     // ❌ Verbose
if (user.active != false) { }    // ❌ Verbose
```

**Fix:**

```javascript
if (user.active) { }              // ✅ Concise
if (!user.active) { }             // ✅ Concise negation
```

---

### ScriptEmptyFunctionRule

**Severity:** ℹ️ADVICE
**Description:** Detects empty function bodies
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Empty functions are usually placeholder code that was never implemented or handlers that were meant to do something but don't. They add confusion (developers wonder if they're intentional), increase code size unnecessarily (which have hard limits!), and can mask missing functionality. Either implement them or remove them to keep your codebase clean and intentional.

**What it catches:**

- Functions with empty bodies
- Placeholder functions that should be implemented or removed

**Example violations:**

```javascript
function processData(data) {
    // ❌ Empty function body
}

const handler = function() { }; // ❌ Empty function
```

---

### ScriptOnSendSelfDataRule

**Severity:** ℹ️ADVICE
**Description:** Detects anti-pattern of using self.data as temporary storage in outbound endpoint onSend scripts
**Applies to:** PMD outbound endpoint onSend scripts

**Why This Matters:**

Using `self.data` as temporary storage in onSend scripts is an anti-pattern that obscures intent and pollutes the `self` reference with unnecessary properties. When developers write patterns like `self.data = {:}` followed by building up that object and returning it, they're using the endpoint's `self` reference as a temporary variable holder instead of using proper local variables.

**This makes code harder to understand** because readers must determine whether `self.data` contains important endpoint state or is just temporary storage. It also makes testing and debugging more difficult since the `self` object is being mutated unnecessarily.

**What This Rule Does:**
This rule detects when `self.data` is **assigned a new object** (empty or populated) in outbound endpoint onSend scripts. This pattern indicates the developer is using `self.data` as temporary storage. Property assignments to existing data like `self.data.foo = 'bar'` are allowed (for cases where data comes from valueOutBinding).

**Intent:** Encourage clear, maintainable code by using local variables instead of polluting the `self` reference with temporary storage.

**What it catches:**

- `self.data = {:}` - Using self.data as temporary storage (empty object)
- `self.data = {'foo': 'bar'}` - Using self.data as temporary storage (populated object)
- Any assignment that creates a new `self.data` object

**What it allows:**

- `self.data.foo = 'bar'` - Property assignment to existing data (✅ OK - assumes self.data created from valueOutBinding)
- `self.data.nested.value = 123` - Nested property assignment (✅ OK)
- Creating local variables: `let postData = {:}` (✅ Recommended)

**Example violations:**

```javascript
// ❌ Anti-pattern - Using self.data as temporary storage
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      self.data = {:};  // Pollutes self reference
      self.data.foo = 'bar';
      self.data.baz = computeValue();
      return self.data;  // Returns temporary storage
    %>"
  }]
}
```

```javascript
// ❌ Anti-pattern - Using self.data as temporary storage with initial values
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      self.data = {'name': 'John', 'age': 30};  // Unnecessary use of self reference
      return self.data;
    %>"
  }]
}
```

**Fix:**

```javascript
// ✅ Good - Use local variable for clarity
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      let postData = {:};  // Clear intent: local temporary variable
      postData.name = 'John';
      postData.age = 30;
      postData.computed = computeValue();
      return postData;  // Return the local variable
    %>"
  }]
}
```

```javascript
// ✅ Good - Property assignment when data exists from valueOutBinding
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      // Assumes self.data already has values from valueOutBinding
      self.data.additionalField = 'computed value';  // Adding to existing data
      return self.data;
    %>"
  }]
}
```

```javascript
// ✅ Good - Direct return when data is simple
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      return {'name': 'John', 'age': 30};  // No temporary storage needed
    %>"
  }]
}
```

**Note:** This rule only applies to **outbound** endpoints. Inbound endpoints are not checked. Comments containing the pattern are automatically ignored.

---

### ScriptUnusedFunctionRule

**Severity:** ℹ️ADVICE
**Description:** Detects functions that are declared but never called
**Applies to:** PMD embedded scripts (`<% ... %>`) and Pod endpoint/widget scripts ONLY

**Why This Matters:**

Unused functions add unnecessary code that developers must read and maintain, creating mental overhead when trying to understand what the page actually does. They also increase parsing time and memory usage. Removing unused functions keeps your PMD/Pod files focused and makes the actual logic easier to follow.

**What This Rule Does:**
This rule tracks function usage within PMD and Pod files. Unlike standalone `.script` files that use export patterns, embedded scripts don't have formal exports. This rule identifies function variables that are declared but never called anywhere in the script or across related script sections in the same file.

**Intent:** Identify unused functions that can be safely removed to reduce code complexity.

**What it catches:**

- Function variables declared but never called
- Functions that were intended to be used but aren't referenced
- Dead code that should be removed

**Example violations:**

```javascript
// In myPage.pmd
<%
  const processData = function(data) {  // ✅ Used below
    return data.filter(item => item.active);
  };
  
  const unusedHelper = function(val) {  // ❌ Never called - unused function
    return val * 2;
  };
  
  const results = processData(pageVariables.items);
%>
```

**Fix:**

```javascript
// In myPage.pmd
<%
  const processData = function(data) {  // ✅ Used
    return data.filter(item => item.active);
  };
  
  // ✅ Removed unusedHelper - it was never called
  
  const results = processData(pageVariables.items);
%>
```

**Note:** This rule is separate from `ScriptDeadCodeRule`, which validates export patterns in standalone `.script` files. Use `ScriptDeadCodeRule` for `.script` files and `ScriptUnusedFunctionRule` for embedded scripts in PMD/Pod files.

---

### ScriptUnusedFunctionParametersRule

**Severity:** ℹ️ADVICE
**Description:** Detects unused function parameters
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Unused parameters make function signatures misleading - callers think they need to pass values that are actually ignored. This wastes developer time figuring out what to pass and creates confusion about the function's actual requirements. Removing unused parameters clarifies the API and prevents wasted effort.

**What it catches:**

- Function parameters that are declared but never used
- Parameters that could be removed to simplify the function signature

**Example violations:**

```javascript
function processUser(user, preferences) { // ❌ preferences unused
    return user.name;
}
```

**Fix:**

```javascript
function processUser(user) { // ✅ Only used parameters
    return user.name;
}
```

---

### ScriptUnusedVariableRule

**Severity:** ℹ️ADVICE
**Description:** Ensures all declared variables are used (prevents dead code)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Unused variables clutter code and create confusion - developers waste time wondering if the variable is actually used somewhere they can't see. They also suggest incomplete refactoring or abandoned features. Removing unused variables improves code clarity and reduces the mental load of understanding what's actually active in your application.

**What it catches:**

- Variables declared but never used
- Dead code that increases bundle size

**Example violations:**

```javascript
function processData() {
    const unusedVar = "never used"; // ❌ Unused variable
    const result = calculateResult();
    return result;
}
```

**Fix:**

```javascript
function processData() {
    const result = calculateResult();
    return result;
}
```

---

### ScriptUnusedIncludesRule

**Severity:** ℹ️ADVICE
**Description:** Detects script files that are included but never used in PMD files
**Applies to:** PMD files with script includes

**Why This Matters:**

Including unused script files forces the engine to parse and load code that's never executed, directly impacting page load time. Each unnecessary include adds to your application's bundle size and slows down the initial page render. Removing unused includes makes pages load faster and removes potential developer confusion as to why the script is being included in the first place.

**What it catches:**

- Script files in PMD include arrays that are never called
- Dead script dependencies that increase bundle size

**Example violations:**

```javascript
// In sample.pmd
{
  "include": ["util.script", "helper.script"], // ❌ helper.script never called
  "onLoad": "<%
    pageVariables.winningNumbers = util.getFutureWinningLottoNumbers(); // Only util.script is used
  %>"
}
```

**Fix:**

```javascript
// In sample.pmd
{
  "include": ["util.script"], // ✅ Only include used scripts
  "onLoad": "<%
    pageVariables.winningNumbers = util.getFutureWinningLottoNumbers();
  %>"
}
```

---

### HardcodedApplicationIdRule

**Severity:** ℹ️ADVICE
**Description:** Detects Hardcoded applicationId values that should be replaced with site.applicationId
**Applies to:** PMD and Pod files

**Why This Matters:**

Hardcoded application IDs break when you deploy the same code to different customer environments, because each has a unique ID. Using `site.applicationId` makes your code environment-agnostic and prevents runtime failures.

**What it catches:**

- Hardcoded applicationId values in scripts and configurations
- Values that should use site.applicationId instead

**Example violations:**

```javascript
const appId = "acmeCorp_speedy"; // ❌ Hardcoded applicationId
```

**Fix:**

```javascript
const appId = site.applicationId; // ✅ Use site.applicationId
```

---

### EmbeddedImagesRule

**Severity:** ℹ️ADVICE
**Description:** Detects embedded images that should be stored as external files
**Applies to:** PMD and Pod files

**Why This Matters:**

Base64-encoded images bloat your PMD/Pod file sizes dramatically (often 30% larger than the image itself) and make files harder to version control since small image changes create large text diffs. External images load faster, cache better, and keep your code files focused on logic. This significantly improves page load performance and makes code reviews manageable.

**What it catches:**

- Base64 encoded images embedded directly in files
- Images that should be stored as external files

**Example violations:**

```json
{
  "type": "image",
  "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." // ❌ Embedded image
}
```

**Fix:**

```json
{
  "type": "image", 
  "url": "http://example.com/images/logo.png" // ✅ External image file
}
```

---

### HardcodedWidRule

**Severity:** ℹ️ADVICE
**Description:** Detects Hardcoded WID (Workday ID) values that should be configured in app attributes
**Applies to:** PMD and Pod files

**Why This Matters:**

Hardcoded WIDs (Workday IDs) are environment-specific - a worker or job WID from your WCPDev tenant won't exist in Production. This causes runtime errors when the code tries to look up non-existent data. But even if you're using a common WID that exists across environments, it is meaningless to a developer looking at your code (possibly including yourself!). Storing WIDs in app attributes allows different values per environment, makes your application portable across tenants and instances, and allows for you to name it in a way that makes sense!

**What it catches:**

- Hardcoded 32-character WID values
- WIDs that should be configured in app attributes

**Example violations:**

```javascript
const query = "SELECT worker FROM allIndexedWorkers WHERE country = 'd9e41a8c446c11de98360015c5e6daf6'"; // ❌ Hardcoded WID
```

**Fix:**

```javascript
const usaLocation = appAttr.usaLocation; // ✅ Use app attribute
const query = "SELECT worker FROM allIndexedWorkers WHERE country = usaLocation"
```

**Configuration:**

- **`allow_wid_in_task_report_link_fields`** (boolean, default: false): When true, hardcoded WIDs in the `wid` field (used by Workday task/report link functionality) are not reported. Leave false to flag all hardcoded WIDs; set true if your app uses task or report links that require a WID in that field.

```json
{
  "HardcodedWidRule": {
    "enabled": true,
    "custom_settings": {
      "allow_wid_in_task_report_link_fields": false
    }
  }
}
```

---

### HardcodedWorkdayAPIRule

**Severity:** 🚨ACTION
**Description:** Detects Hardcoded *.workday.com URLs that should use apiGatewayEndpoint for regional awareness
**Applies to:** AMD dataProviders, PMD inbound/outbound endpoints, POD endpoints

**Why This Matters:**

Hardcoded workday.com URLs are not update safe and lack regional awareness. Using the `apiGatewayEndpoint` variable ensures your endpoints work across all environments and regions without code changes. If Workday adds additional regional endpoints or changes infrastructure, using the `apiGatewayEndpoint` application variable keeps your app update safe and regionally aware.

**What it catches:**

- Hardcoded *.workday.com URLs in AMD dataProviders
- Hardcoded *.workday.com URLs in PMD inbound and outbound endpoint URLs
- Hardcoded *.workday.com URLs in POD endpoint URLs
- URLs that should use apiGatewayEndpoint variable instead

**Example violations:**

```json
// AMD dataProvider
{
  "dataProviders": [
    {
      "key": "workday-common",
      "value": "https://api.workday.com/common/v1/"  // ❌ Hardcoded workday.com URL
    }
  ]
}

// PMD endpoint
{
  "name": "getWorker",
  "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com URL
}

// POD endpoint
{
  "name": "updateWorker", 
  "url": "https://api.workday.com/hcm/v1/workers"  // ❌ Hardcoded workday.com URL
}
```

**Fix:**

```json
// AMD dataProvider
{
  "dataProviders": [
    {
      "key": "workday-common",
      "value": "<% apiGatewayEndpoint + '/common/v1/' %>"  // ✅ Use apiGatewayEndpoint
    }
  ]
}

// PMD/POD endpoint
{
  "name": "getWorker",
  "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"  // ✅ Use apiGatewayEndpoint
}
```

---

## 🏗️ Structure Rules

*The Structure Rules bind the outer wards and conduits of your magical constructs. These architectural validations ensure your endpoints, widgets, and configurations form a harmonious and secure foundation for your mystical applications.*

*These rules validate widget configurations, endpoint structures, component compliance, Hardcoded values, file naming conventions, and PMD organization in both PMD and Pod files. They also apply to orchestration and suborchestration files; some rules apply only to certain flow types (e.g. security domain only to Sync/Async).*

### EndpointFailOnStatusCodesRule

**Severity:** 🚨ACTION
**Description:** Ensures endpoints properly handle 400 and 403 error status codes
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

Without proper error handling (failOnStatusCodes), your endpoints silently swallow errors like "400 Bad Request" or "403 Forbidden", causing your application to proceed as if the call succeeded when it actually failed. This leads to data inconsistencies, broken workflows, and debugging nightmares. Explicit error handling ensures failures are properly caught and handled.

**What it catches:**

- Missing error handling for 4xx status codes that Extend doesn't treat as failures by default

**Example violations:**

```json
{
  "endPoints": [{
    "name": "getCurrentUser",
    "url": "/users/me"
    // ❌ Missing failOnStatusCodes
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getCurrentUser", 
    "url": "/users/me",
    "failOnStatusCodes": [
      {"code": 400},
      {"code": 403}
    ]
  }]
}
```

---

### NoIsCollectionOnEndpointsRule

**Severity:** 🚨ACTION
**Description:** Detects isCollection: true on inbound endpoints which can cause performance issues
**Applies to:** PMD inbound endpoints and Pod endpoints

**What it catches:**

- Inbound endpoints with `isCollection: true`

**Why This Matters:**

Using `isCollection: true` on inbound endpoints may cause severe performance degradation when apps are in use simultaneously by different users. This can slow down the entire Workday instance for all users, not just your application. Avoiding isCollection on inbound endpoints is critical for maintaining app performance.

**Example violations:**

```json
{
  "inboundEndpoints": [
    {
      "name": "getWorkers",
      "isCollection": true  // ❌ May cause performance issues
    }
  ]
}
```

**Fix:**

Consider utilizing WQL or RaaS instead, which will allow for fewer API calls that return larger datasets.

---

### OnlyMaximumEffortRule

**Severity:** 🚨ACTION
**Description:** Ensures endpoints do not use bestEffort to prevent masked API failures
**Applies to:** PMD inbound and outbound endpoints, and Pod endpoints

**What it catches:**

- Endpoints with `bestEffort: true` on inbound and outbound endpoints
- Includes PMD and POD endpoints

**Why This Matters:**

Using `bestEffort: true` on endpoints silently swallows API failures, causing your code to continue executing as if the call succeeded when it actually failed. This leads to data inconsistency, partial updates, and bugs that are extremely hard to debug because you have no visibility into the failure.

**Example violations:**

```json
{
  "name": "getWorkers",
  "bestEffort": true  // ❌ Can mask API failures
}
```

**Fix:**

```json
{
  "name": "getWorkers"
  // ✅ Remove bestEffort property
}
```

---

### NoPMDSessionVariablesRule

**Severity:** 🚨ACTION
**Description:** Detects outboundVariable endpoints with variableScope: session which can cause performance degradation
**Applies to:** PMD outbound endpoints only

**What it catches:**

- Outbound endpoints with `type: "outboundVariable"` AND `variableScope: "session"`

**Why This Matters:**

Session-scoped variables persist for the entire user session (potentially hours), continuously consuming memory even after the user leaves your page. This memory isn't released until logout, degrading performance over time and potentially causing issues for long-running sessions.

**Example violations:**

```json
{
  "outboundEndpoints": [
    {
      "name": "saveUserPreference",
      "type": "outboundVariable",
      "variableScope": "session"  // ❌ Lasts entire session - performance issue
    }
  ]
}
```

**Fix:**

```json
{
  "outboundEndpoints": [
    {
      "name": "saveUserPreference",
      "type": "outboundVariable",
      "variableScope": "flow"  // ✅ Use a flow variable, instead
    }
  ]
}
```

---

### EndpointNameLowerCamelCaseRule

**Severity:** ℹ️ADVICE
**Description:** Ensures endpoint names follow lowerCamelCase convention
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

LowerCamelCase is the Workday Extend standard for endpoint names. Following the convention improves team collaboration and makes code more professional.

**What it catches:**

- Endpoint names that don't follow camelCase naming
- Inconsistent naming conventions across endpoints

**Example violations:**

```json
{
  "endPoints": [
    {
      "name": "get_user_data"  // ❌ snake_case
    }, 
    {
      "name": "GetUserProfile" // ❌ PascalCase
    }
  ]
}
```

**Fix:**

```json
{
  "endPoints": [
    {
      "name": "getUserData"    // ✅ lowerCamelCase
    }, 
    {
      "name": "getUserProfile" // ✅ lowerCamelCase
    }
  ]
}
```

---

### EndpointBaseUrlTypeRule

**Severity:** ℹ️ADVICE
**Description:** Ensures endpoint URLs for Workday APIs utilize dataProviders and baseUrlType
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

Workday APIs are heavily used within most Extend applications. Creating a re-usable definition in the AMD dataProviders array is recommended. When dataProviders are defined, developers can use `baseUrlType` on inbound and outbound endpoints (like 'workday-common' or 'workday-app'). This prevents the developer from explicitly including the entire URL both within and across pages. It has the added benefit of reducing the length of URLs on your endpoint definitions, making them easier to read and maintain.

**What it catches:**

- Hardcoded *.workday.com domains in endpoint URLs
- Hardcoded apiGatewayEndpoint values in URLs
- Endpoints that should use baseUrlType instead of Hardcoded values
- Both patterns promote extracting Workday endpoints to shared AMD data providers

**Example violations:**

```json
// Hardcoded workday.com URL
{
  "name": "getWorker",
  "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com
}

// Direct apiGatewayEndpoint usage
{
  "name": "getWorker",
  "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"  // ❌ Should use baseUrlType
}
```

**Fix:**

```json
{
  "name": "getWorker",
  "url": "/workers/me",  // ✅ Relative URL
  "baseUrlType": "workday-common"  // ✅ Use baseUrlType instead
}
```

---

### PMDSectionOrderingRule

**Severity:** ℹ️ADVICE
**Description:** Ensures PMD file root-level sections follow consistent ordering
**Applies to:** PMD file structure
**Configurable:** ✅ Top-level section order and enforcement can be customized

**Why This Matters:**

Consistent section ordering across PMD files makes them easier to navigate and review. When every file follows the same structure, developers can quickly find what they're looking for (endpoints, scripts, presentation) without scanning the entire file. This is especially helpful when reviewing code or onboarding new team members who need to understand unfamiliar pages.

**What it catches:**

- PMD sections in non-standard order
- Inconsistent file structure across applications

**Default Section Order:**

1. `id`
2. `securityDomains`
3. `include`
4. `script`
5. `endPoints`
6. `onSubmit`
7. `outboundData`
8. `onLoad`
9. `presentation`

**Example violations:**

```json
{
  "presentation": { },     // ❌ presentation should come last
  "id": "myAppPage",
  "script": "<%  %>",
  "include": ["util.script"]
}
```

**Fix:**

```json
{
  "id": "myAppPage",         // ✅ Proper order
  "include": ["util.script"],
  "script": "<%  %>",
  "presentation": { }
}
```

**Configuration:**

```json
{
  "PMDSectionOrderingRule": {
    "enabled": true,
    "custom_settings": {
        "section_order": ["id", "securityDomains", "include", "script", "endPoints", "onSubmit", "outboundData", "onLoad", "presentation"]
    }
  }
}
```

---

### PMDSecurityDomainRule

**Severity:** 🚨ACTION
**Description:** Ensures PMD pages have at least one security domain defined (excludes microConclusion and error pages unless strict mode is enabled)
**Applies to:** PMD file security configuration

**Why This Matters:**

Security domains control who can access your PMD pages in Workday. Missing security domains means your page is accessible to all users, which could lead to a security incident.

**What it catches:**

- PMD pages missing `securityDomains` list
- Empty `securityDomains` arrays
- Enforces security best practices for Workday applications

**Smart Exclusions (configurable):**

- **MicroConclusion pages**: Pages with `presentation.microConclusion: true` are excluded (unless strict mode)
- **Error pages**: Pages whose ID appears in SMD `errorPageConfigurations` are excluded (unless strict mode)
- Only enforces security domains on pages that actually need them (unless strict mode)

**Example violations:**

```javascript
// ❌ Missing security domains
{
  "id": "myPage",
  "presentation": {
    "body": { ... }
  }
}

// ✅ Proper security domains
{
  "id": "myPage", 
  "securityDomains": ["ViewAdminPages"],
  "presentation": {
    "body": { ... }
  }
}

// ✅ MicroConclusion page (excluded in normal mode)
{
  "id": "microPage",
  "presentation": {
    "microConclusion": true,
    "body": { ... }
  }
}
```

**Configuration:**

- **`strict`** (boolean, default: false): When enabled, requires security domains for ALL PMD pages, including microConclusion and error pages
  - `false`: Normal mode with smart exclusions (default for all presets)
  - `true`: Strict mode requiring security domains for all pages (opt-in only)

**Configuration:**

```json
{
  "PMDSecurityDomainRule": {
    "enabled": true,
    "custom_settings": {
      "strict": true
    }
  }
}
```

---

### OrchestrationSecurityDomainRule

**Severity:** 🚨ACTION
**Description:** Ensures Synchronous and Asynchronous orchestrations have at least one security domain defined
**Applies to:** Sync and Async Orchestration templates only; Suborchestrations are not checked by this rule.

**Why This Matters:**

Security domains control access to orchestrations in Workday. Sync and Async flows must define a security domain. Business Process Triggered, Integration, and Suborchestrations are not checked by this rule, as they do not currently support security domains.

**What it catches:**

- Sync/Async orchestrations with missing `securityDomains`

**Example message:**

Orchestration 'myFlow' must define at least one security domain (securityDomains).

**Configuration:** No custom settings.

---

### OrchestrationGlobalErrorHandlerRule

**Severity:** 🚨 ACTION
**Description:** Ensures orchestrations have a global error handler for uncaught or propagated errors.
**Applies to:** Orchestration files only. Applies to Sync, Async, Business Process Triggered, and Integration flow types. Suborchestrations are not checked because they do not support global handlers.

**Why This Matters:**

A global error handler is required when an uncaught error occurs or when a local (step-level) error handler propagates the error. The global handler is the safety net.

**What it catches:**

- Orchestrations (Sync, Async, BPT, Integration) with missing top-level (global) `errorHandler`
- Step-level error handlers alone do not satisfy this rule (e.g. a flow with only a step error handler still yields a finding)

**Example message:**

Orchestration 'myFlow' must have a global error handler.

**Configuration:** No custom settings.

---

### WidgetIdRequiredRule

**Severity:** 🚨ACTION
**Description:** Ensures all widgets have an 'id' field set
**Applies to:** PMD and POD widget structures
**Configurable:** ✅ Custom widget type exclusions can be configured

**Why This Matters:**

Widget IDs are essential for referencing widgets in scripts (to get/set values, show/hide, etc.) and for debugging. Without IDs, you can't interact with widgets programmatically, making dynamic behavior impossible. IDs also help identify widgets in error messages and make code maintenance much easier when you need to find where a widget is defined or used. There are also known issues where missing IDs will result in logs not showing the data someone may expect (i.e. a panelList widget may not log its values without all IDs set).

**What it catches:**

- Widgets missing required `id` field

**Smart Exclusions:**

Built-in widget types that don't require IDs: `footer`, `item`, `group`, `title`, `pod`, `cardContainer`, `card`, `instanceList`, `taskReference`, `editTasks`, `multiSelectCalendar`, `bpExtender`, `hub`, and column objects (which use `columnId` instead).

**Configuration:**

You can add additional widget types to exclude from ID requirements:

```json
{
  "WidgetIdRequiredRule": {
    "enabled": true,
    "custom_settings": {
      "excluded_widget_types": ["section", "fieldSet"]
    }
  }
}
```

**Example violations:**

```json
{
  "type": "richText",  // ❌ Missing id field
  "label": "Welcome",
  "value": "Hello, user!"
}
```

**Fix:**

```json
{
  "type": "richText",
  "id": "welcomeMessage",  // ✅ Added id field
  "label": "Welcome",
  "value": "Hello, user!"
}
```

---

### WidgetIdLowerCamelCaseRule

**Severity:** ℹ️ADVICE
**Description:** Ensures widget IDs follow lowerCamelCase naming convention
**Applies to:** PMD and POD widget structures

**Why This Matters:**

LowerCamelCase is the Workday standard, and following it means your code will be consisten across pages AND applications. Mixing conventions (snake_case, PascalCase) forces constant reference checking and slows development.

**What it catches:**

- Widget IDs that don't follow lowerCamelCase convention
- Style guide violations

**Example violations:**

```json
{
  "type": "richText",
  "id": "WelcomeMessage"  // ❌ Should be lowerCamelCase
}
```

**Fix:**

```json
{
  "type": "richText",
  "id": "welcomeMessage"  // ✅ Proper lowerCamelCase
}
```

---

### FooterPodRequiredRule

**Severity:** ℹ️ADVICE
**Description:** Ensures footer uses pod structure (direct pod or footer with pod children)
**Applies to:** PMD file footer sections

**Why This Matters:**

Using pods for footers promotes component reuse and consistency across your application. Pods are designed to be reusable components, and structuring footers as pods makes them easier to maintain centrally and update across multiple pages. For many applications, developers include an image for the footer. Being able to change the values for this across all pages at once reduces risk when making updates, easing the maintenance for developers.

**What it catches:**

- Missing pod widgets in footers
- Inconsistent footer implementations

**Smart Exclusions:**

Pages with tabs, hub pages, and microConclusion pages are excluded from this requirement.

**Example violations:**

```json
{
  "presentation": {
    "footer": {
      "type": "footer",
      "children": [
        {
          "type": "richText",  // ❌ Should be pod
          "id": "footerText"
        }
      ]
    }
  }
}
```

**Fix:**

```json
{
  "presentation": {
    "footer": {
      "type": "footer",
      "children": [
        {
          "type": "pod",  // ✅ Using pod structure
          "podId": "footer"
        }
      ]
    }
  }
}
```

---

### StringBooleanRule

**Severity:** ℹ️ADVICE
**Description:** Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans
**Applies to:** PMD and POD file structures

**Why This Matters:**

Booleans should be represented as actual boolean values (true / false), not strings ("true" / "false").
While the backend may gracefully cast string values, this “magic conversion” hides the true intent of the data.

> 🧙 **Wizard's Note:** Some areas of Extend actually *require* you to use strings, instead of bools (for example: for some values in your AMD flows), so we won't check in those places and just accept this "gotcha" with Extend.

**What it catches:**

- Boolean values represented as strings `"true"` or `"false"`

**Example violations:**

```json
{
  "visible": "true",  // ❌ String instead of boolean
  "enabled": "false"  // ❌ String instead of boolean
}
```

**Fix:**

```json
{
  "visible": true,  // ✅ Actual boolean
  "enabled": false  // ✅ Actual boolean
}
```

---

### FileNameLowerCamelCaseRule

**Severity:** ℹ️ADVICE
**Description:** Ensures all file names follow lowerCamelCase naming convention
**Applies to:** All files (PMD, POD, Script)

**Why This Matters:**

LowerCamelCase is the Workday Extend standard, and following it ensures files are organized predictably, keeping your code looking professional.

**What it catches:**

- Files using PascalCase (e.g., `MyPage.pmd`)
- Files using snake_case (e.g., `my_page.pmd`)
- Files using UPPERCASE (e.g., `MYPAGE.pmd`)
- Files starting with numbers (e.g., `2myPage.pmd`)

**Valid naming patterns:**

- **Pure lowerCamelCase**: `myPage.pmd`, `helperFunctions.script`

**Example violations:**

```
MyPage.pmd              // ❌ PascalCase - should be: myPage.pmd
worker_detail.pmd       // ❌ snake_case - should be: workerDetail.pmd
FOOTER.pod              // ❌ UPPERCASE - should be: footer.pod
2myPage.pmd             // ❌ Starts with number
helper_functions.script // ❌ snake_case - should be: helperFunctions.script
```

**Valid examples:**

```
myPage.pmd              // ✅ lowerCamelCase
helperFunctions.script  // ✅ lowerCamelCase
footer.pod              // ✅ lowerCamelCase
```

**Fix:**

Rename files to follow lowerCamelCase convention.

---

### MultipleStringInterpolatorsRule

**Severity:** ℹ️ADVICE
**Description:** Detects multiple string interpolators in a single string which should use template literals instead
**Applies to:** PMD and POD files

**What it catches:**

- Strings with 2 or more `<% %>` interpolators
- String values that mix static text with multiple dynamic values
- Does NOT flag strings already using template literals (backticks with `{{}}`)

**Why This Matters:**

Multiple interpolators (`<% name %> and <% age %>`) create multiple parse operations and are harder to read than a single template literal. Using one interpolator with a template literal (`<% \`Name: {{name}}, Age: {{age}}\` %>`) is cleaner and easier to maintain.

**Example violations:**

```json
{
  "value": "My name is <% name %> and I like <% food %>"  // ❌ 2 interpolators
}

{
  "label": "Name: <% firstName %>, Age: <% age %>, City: <% city %>"  // ❌ 3 interpolators
}
```

**Fix:**

```json
{
  "value": "<% `My name is {{name}} and I like {{food}}` %>"  // ✅ SINGLE interpolator with template literal
}

{
  "label": "<% `Name: {{firstName}}, Age: {{age}}, City: {{city}}` %>"  // ✅ SINGLE interpolator with template literal
}
```

**Note:** Use ONE `<% %>` interpolator containing a template literal with backticks (\`) and `{{}}` for variables.

---

### GridPagingWithSortableFilterableRule

**Severity:** 🚨ACTION
**Description:** Detects grids with paging and sortableAndFilterable columns which can cause performance issues
**Applies to:** PMD and POD grid widgets

**Why This Matters:**

Combining paging with sortableAndFilterable columns forces Workday to load and process the entire dataset client-side for sorting/filtering, defeating the purpose of paging. This can cause severe performance degradation with large datasets. Either disable paging or remove sortableAndFilterable to prevent performance issues.

**What it catches:**

- Grid widgets with `autoPaging: true` OR `pagingInfo` present
- AND any column with `sortableAndFilterable: true`

**Example violations:**

```json
{
  "type": "grid",
  "id": "workersGrid",
  "autoPaging": true,  // Or "pagingInfo": {}
  "columns": [
    {
      "columnId": "workerNameColumnId",
      "sortableAndFilterable": true  // ❌ With paging, this causes major performance issues
    },
    {
      "columnId": "departmentColumnId",
      "sortableAndFilterable": true  // ❌ Also flagged
    }
  ]
}
```

**Fix - Option 1 (Remove paging):**

```json
{
  "type": "grid",
  "id": "workersGrid",
  // ✅ Removed autoPaging/pagingInfo
  "columns": [
    {
      "columnId": "workerName",
      "sortableAndFilterable": true  // ✅ OK without paging
    }
  ]
}
```

**Fix - Option 2 (Remove sortableAndFilterable):**

```json
{
  "type": "grid",
  "id": "workersGrid",
  "autoPaging": true,
  "columns": [
    {
      "columnId": "workerName",
      "sortableAndFilterable": false  // ✅ Disabled sorting/filtering
    }
  ]
}
```

---

## 📊 Quick Reference

| Rule Name                                      | Category  | Severity    | Default Enabled | Key Settings                                           |
| ---------------------------------------------- | --------- | ----------- | --------------- | ------------------------------------------------------ |
| **ScriptVarUsageRule**                   | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptDeadCodeRule**                   | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptComplexityRule**                 | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptLongFunctionRule**               | Script    | ℹ️ ADVICE | ✅              | `max_lines`, `skip_comments`, `skip_blank_lines`      |
| **ScriptFunctionParameterCountRule**     | Script    | ℹ️ ADVICE | ✅              | `max_parameters`                                      |
| **ScriptFunctionParameterNamingRule**    | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptUnusedVariableRule**             | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptUnusedFunctionParametersRule**   | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptUnusedFunctionRule**             | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptVariableNamingRule**             | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptConsoleLogRule**                 | Script    | 🚨 ACTION | ✅              | —                                                     |
| **ScriptEmptyFunctionRule**              | Script    | 🚨 ACTION | ✅              | —                                                     |
| **ScriptNestingLevelRule**               | Script    | ℹ️ ADVICE | ✅              | `max_nesting`                                         |
| **ScriptLongBlockRule**                  | Script    | ℹ️ ADVICE | ✅              | `max_lines`, `skip_comments`, `skip_blank_lines`      |
| **ScriptMagicNumberRule**                | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptStringConcatRule**               | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptArrayMethodUsageRule**           | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptNestedArraySearchRule**          | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptDescriptiveParameterRule**       | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptFunctionReturnConsistencyRule**  | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptVerboseBooleanCheckRule**        | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **StringBooleanRule**                    | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptUnusedIncludesRule**             | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **ScriptOnSendSelfDataRule**             | Script    | ℹ️ ADVICE | ✅              | —                                                     |
| **EndpointFailOnStatusCodesRule**        | Structure | 🚨 ACTION | ✅              | —                                                     |
| **EndpointNameLowerCamelCaseRule**       | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **EndpointBaseUrlTypeRule**              | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **WidgetIdRequiredRule**                 | Structure | 🚨 ACTION | ✅              | `excluded_widget_types`                               |
| **WidgetIdLowerCamelCaseRule**           | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **HardcodedApplicationIdRule**           | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **HardcodedWidRule**                     | Structure | ℹ️ ADVICE | ✅              | `allow_wid_in_task_report_link_fields`                 |
| **PMDSectionOrderingRule**               | Structure | ℹ️ ADVICE | ✅              | `required_order`                                      |
| **PMDSecurityDomainRule**                | Structure | 🚨 ACTION | ✅              | `strict`                                              |
| **OrchestrationSecurityDomainRule**     | Structure | 🚨 ACTION | ✅              | —                                                     |
| **OrchestrationGlobalErrorHandlerRule** | Structure | 🚨 ACTION | ✅              | —                                                     |
| **EmbeddedImagesRule**                   | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **FooterPodRequiredRule**                | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **HardcodedWorkdayAPIRule**              | Structure | 🚨 ACTION | ✅              | —                                                     |
| **FileNameLowerCamelCaseRule**           | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **NoIsCollectionOnEndpointsRule**        | Structure | 🚨 ACTION | ✅              | —                                                     |
| **OnlyMaximumEffortRule**                | Structure | 🚨 ACTION | ✅              | —                                                     |
| **NoPMDSessionVariablesRule**            | Structure | 🚨 ACTION | ✅              | —                                                     |
| **MultipleStringInterpolatorsRule**      | Structure | ℹ️ ADVICE | ✅              | —                                                     |
| **GridPagingWithSortableFilterableRule** | Structure | 🚨 ACTION | ✅              | —                                                     |

---

---

## Rule Configuration

All rules can be configured in your configuration files:

- **`configs/presets/production-ready.json`** - Standard configuration
- **`configs/presets/development.json`** - Some rules disabled for in-development stage

### Configuration Options

Each rule supports:

- **`enabled`** - Enable/disable the rule
- **`severity_override`** - Override default severity (ACTION, ADVICE)
- **`custom_settings`** - Rule-specific configuration options

### Example Configuration

```json
{
  "ScriptComplexityRule": {
    "enabled": true,
    "severity_override": "ACTION",
    "custom_settings": {
      "max_complexity": 8
    }
  },
  "PMDSectionOrderingRule": {
    "enabled": true,
    "custom_settings": {
      "section_order": ["id", "presentation", "script"]
    }
  }
}
```

---

## Summary

The Arcane Auditor channels mystical powers through **42 rules** across **2 categories**:

- ✅ **Script Rules** - Code quality for PMD and standalone scripts
- ✅ **Structure Rules** - Widget configurations, endpoint validation, structural compliance, Hardcoded values, and PMD organization

**Severity Distribution:**

- **10 ACTION Rules**: Potentially critical issues requiring immediate attention
- **32 ADVICE Rules**: Recommendations for code quality and best practices

These rules help maintain consistent, high-quality Workday Extend applications by catching issues that compilers aren't designed to catch, but are important for maintainability, performance, and team collaboration.
