# Arcane Auditor Rules Grimoire 📜

*Ancient wisdom distilled into 42 mystical validation rules*

This grimoire provides a comprehensive overview of all **42 validation rules** wielded by the Arcane Auditor. These enchantments help reveal hidden code quality issues, style violations, and structural problems that compilers don't detect but are essential for master code wizards to identify.

## 📋 Table of Contents

### Script Rules

- [ScriptArrayMethodUsageRule](#scriptarraymethodusagerule)
- [ScriptComplexityRule](#scriptcomplexityrule)
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
- [ScriptNullSafetyRule](#scriptnullsafetyrule)
- [ScriptOnSendSelfDataRule](#scriptonsendselfdatarule)
- [ScriptStringConcatRule](#scriptstringconcatrule)
- [ScriptUnusedFunctionParametersRule](#scriptunusedfunctionparametersrule)
- [ScriptUnusedFunctionRule](#scriptunusedfunctionrule)
- [ScriptUnusedScriptIncludesRule](#scriptunusedscriptincludesrule)
- [ScriptUnusedVariableRule](#scriptunusedvariablerule)
- [ScriptVarUsageRule](#scriptvarusagerule)
- [ScriptVariableNamingRule](#scriptvariablenamingrule)
- [ScriptVerboseBooleanCheckRule](#scriptverbosebooleancheckrule)

### Structure Rules

- [AMDDataProvidersWorkdayRule](#amddataprovidersworkdayrule)
- [EmbeddedImagesRule](#embeddedimagesrule)
- [EndpointBaseUrlTypeRule](#endpointbaseurltyperule)
- [EndpointFailOnStatusCodesRule](#endpointfailonstatuscodesrule)
- [EndpointNameLowerCamelCaseRule](#endpointnamelowercamelcaserule)
- [FileNameLowerCamelCaseRule](#filenamelowercamelcaserule)
- [FooterPodRequiredRule](#footerpodrequiredrule)
- [GridPagingWithSortableFilterableRule](#gridpagingwithsortablefilterablerule)
- [HardcodedApplicationIdRule](#hardcodedapplicationidrule)
- [HardcodedWidRule](#hardcodedwidrule)
- [MultipleStringInterpolatorsRule](#multiplestringinterpolatorsrule)
- [NoIsCollectionOnEndpointsRule](#noiscollectiononendpointsrule)
- [NoPMDSessionVariablesRule](#nopmdsessionvariablesrule)
- [OnlyMaximumEffortRule](#onlymaximumeffortrule)
- [PMDSectionOrderingRule](#pmdsectionorderingrule)
- [PMDSecurityDomainRule](#pmdsecuritydomainrule)
- [StringBooleanRule](#stringbooleanrule)
- [WidgetIdLowerCamelCaseRule](#widgetidlowercamelcaserule)
- [WidgetIdRequiredRule](#widgetidrequiredrule)

## Rule Categories

The rules are organized into two main categories:

- **Script Rules**: Code quality and best practices for PMD, Pod, and standalone script files
- **Structure Rules**: Widget configurations, endpoint validation, structural compliance, hardcoded values, and PMD organization

## Severity Levels

Rules use a simplified two-tier severity system:

- 🔴 **ACTION**: Issues that should be addressed immediately
- 🟢 **ADVICE**: Recommendations for code quality and best practices

---

## 🪄 Script Rules

*The Script Rules form the incantations that shape the logic within your enchanted scrolls. These mystical validations ensure your code flows with the elegance and power befitting a master wizard.*

*These rules analyze PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files for comprehensive code quality validation.*

### ScriptVarUsageRule

**Severity:** ADVICE
**Description:** Ensures scripts use 'let' or 'const' instead of 'var' (best practice)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

The `var` keyword has function scope, which can cause unexpected behavior and bugs when the same name is reused in nested blocks. Using `let` (block scope) and `const` (immutable) makes your code more predictable and prevents accidental variable shadowing issues.

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

**Severity:** ADVICE
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
const API_URL = "https://api.example.com";  // ❌ Dead code - constant not exported or used

{
  "getCurrentTime": getCurrentTime  // ❌ unusedHelper and API_KEY are dead code
}
```

**Fix:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };
const helperFunction = function() { return "helper"; };    // ✅ Will be exported
const API_URL = "https://api.example.com";  // ✅ Will be exported

{
  "getCurrentTime": getCurrentTime,
  "helperFunction": helperFunction,
  "API_URL": API_URL  // ✅ All declarations are exported
}
```

**Example with internal usage:**

```javascript
// In util.script
const CACHE_TTL = 3600;  // ✅ Used internally (not exported)
const getCurrentTime = function() { 
  return { "time": date:now(), "ttl": CACHE_TTL };  // Uses CACHE_TTL
};

{
  "getCurrentTime": getCurrentTime  // ✅ CACHE_TTL is used internally
}
```

### ScriptNestingLevelRule

**Severity:** ADVICE
**Description:** Ensures scripts don't have excessive nesting levels (max 4 levels)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Deep nesting (more than 4 levels of if/for/while statements) makes code exponentially harder to read, test, and debug. Each nesting level adds cognitive load, making it difficult to track which conditions are active and increasing the likelihood of logic errors. Flattening nested code through early returns or extracted functions dramatically improves maintainability.

**What it catches:**

- Overly nested code structures (if statements, loops, functions)
- Code that's difficult to read and maintain due to deep nesting

**Example violations:**

```javascript
function processData(data) {
    if (!empty data) { // Level 1
        if (data.isValid) { // Level 2
            if (data.hasContent) { // Level 3
                if (data.content.length > 0) { // Level 4
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

**Severity:** ADVICE
**Description:** Ensures scripts don't have excessive cyclomatic complexity (max 10)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Cyclomatic complexity measures the number of independent paths through your code (every if, else, loop, etc. adds to it). High complexity (>10) means your function has too many decision points, making it exponentially harder to test all scenarios and increasing the chance of bugs. Breaking complex functions into smaller, focused ones makes testing easier and reduces defects.

**What it catches:**

- Functions with too many decision points (if/else, loops, ternary operators, etc.)
- Complex functions that are hard to test and maintain
- Functions that likely need to be broken down

**Example violations:**

```javascript
function processOrder(order) {
    if (order.type == 'premium') {         // +1
        if (order.amount > 1000) {         // +1
            if (order.customer.vip) {      // +1
                // ... complex logic
            } else {                       // +1
                // ... more logic
            }
        } else if (order.amount > 500) {   // +1
            // ... logic
        }
    } else if (order.type == 'standard') { // +1
        for (var i = 0; i < order.items.length; i++) {      // +1
            if (order.items[i].category == 'electronics') { // +1
                // ... logic
            }
        }
    }
    // Complexity: 8+ (getting close to limit)
}
```

**Fix:**

```javascript
function processOrder(order) {
    if (order.type == 'premium') {
        return processPremiumOrder(order);
    }
  
    if (order.type == 'standard') {
        return processStandardOrder(order);
    }
  
    return processBasicOrder(order);
}

function processPremiumOrder(order) {
    // Simplified premium logic
}

function processStandardOrder(order) {
    // Simplified standard logic
}
```

---

### ScriptLongFunctionRule

**Severity:** ADVICE
**Description:** Ensures scripts don't have excessively long functions (max 50 lines)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Functions longer than 50 lines typically violate the single responsibility principle - they're doing too many things. Long functions are harder to understand, test, and reuse, and they often hide bugs in the complexity. Breaking them into smaller, focused functions with clear names makes code self-documenting and easier to maintain.

**What it catches:**

- Functions that exceed 50 lines of code
- Monolithic functions that should be broken down
- Functions that likely violate single responsibility principle

**Example violations:**

```javascript
function processLargeDataset(data) {
    // ... 60 lines of code ...
    // This function is doing too many things
}
```

**Fix:**

```javascript
function processLargeDataset(data) {
    const validated = validateData(data);
    const processed = transformData(validated);
    return formatOutput(processed);
}

function validateData(data) {
    // ... validation logic ...
}

function transformData(data) {
    // ... transformation logic ...
}

function formatOutput(data) {
    // ... formatting logic ...
}
```

---

### ScriptLongBlockRule

**Severity:** ADVICE
**Description:** Ensures non-function script blocks in PMD/POD files don't exceed maximum line count (max 30 lines). Excludes function definitions which are handled by ScriptLongFunctionRule.
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Long script blocks (often found in event handlers, such as onLoad, onChange, or onSend) indicate procedural code that should be refactored into reusable functions. This makes your PMD/Pod files harder to read and the logic harder to test or reuse across pages. Moving logic into functions improves code organization and makes your intent clearer.

**What it catches:**

- Script blocks (in any field including event handlers, such as onLoad, onChange, onSend, etc.) that exceed 30 statements
- Long procedural code that should be refactored into functions
- Script blocks that violate single responsibility principle

**Example violations:**

```javascript
// In onLoad field
<%
    const worker = getWorkerFromEndpoint();
    worker.value = worker.name;
    workerOrg.value = worker.org;
    // ... 35+ statements ...
    pageVariables.referenceData = getReferenceData();
%>
```

**Fix:**

```javascript
// Break into smaller functions
<%
    const worker = getWorkerFromEndpoint(); 
    initializeWorkerPageData(worker);
    setupEventHandlers();
%>

// Define functions elsewhere
function initializeWorkerPageData(worker) {
    worker.value = worker.name;
    workerOrg.value = worker.org;
    // ... smaller, focused logic
}
```

**Configuration:**

The threshold can be customized in config files:

```json
{
  "rules": {
    "ScriptLongBlockRule": {
      "enabled": true,
      "custom_settings": {
        "max_lines": 30
      }
    }
  }
}
```

---

### ScriptFunctionParameterCountRule

**Severity:** ADVICE
**Description:** Ensures functions don't have too many parameters (max 4)
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

**Severity:** ACTION
**Description:** Ensures scripts don't contain console log statements (production code)
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

**Severity:** ADVICE
**Description:** Ensures variables follow lowerCamelCase naming convention
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Consistent naming conventions make code easier to read and reduce cognitive load when switching between files or team members' code. LowerCamelCase is the standard for variables. Consistency enables faster comprehension and fewer mistakes.

**What it catches:**

- Variables that don't follow camelCase naming (snake_case, PascalCase, etc.)
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

**Severity:** ADVICE
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

const processData = function(data_source, target_table) {
    return data_source.map(item => item.process());
};
```

**Fix:**

```javascript
// ✅ lowerCamelCase parameters
const validateUser = function(userId, userName, isActive) {
    return userId && userName && isActive;
};

const processData = function(dataSource, targetTable) {
    return dataSource.map(item => item.process());
};
```

**Real-world example:**

```javascript
// In helperFunctions.script
var isNewDateAfterReferenceDate = function (widget, newDate, referenceDate, message, message_type) {
    // ... function body
};
// ❌ 'message_type' should be 'messageType'
```

**Fix:**

```javascript
// In helperFunctions.script
var isNewDateAfterReferenceDate = function (widget, newDate, referenceDate, message, messageType) {
    // ... function body
};
// ✅ All parameters follow lowerCamelCase convention
```

---

### ScriptArrayMethodUsageRule

**Severity:** ADVICE
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

### ScriptMagicNumberRule

**Severity:** ADVICE
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

### ScriptNullSafetyRule

**Severity:** ACTION
**Description:** Ensures property access chains are protected against null reference exceptions
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Accessing properties on null or undefined objects (`user.address.city` when `user.address` is null) cause runtime errors that can break your entire page. In Workday Extend, this means users see errors instead of their work. Using null coalescing, empty checks, or optional chaining (`user.address.city ?? ''`) provide graceful degradation or defaults when data is missing.

**What it catches:**

- Unsafe property access that could throw null reference exceptions
- Missing null checks before property access
- Improper use of null coalescing operator

**Example violations:**

```javascript
const skill = workerData.skills[0].name;  // ❌ Unsafe - skills could be null/undefined
```

**Fix:**

```javascript
const skills = workerData.skills[0].name ?? '';      // ✅ Null coalescing fallback
```

> **🧙‍♂️ Wizard's Note:** As you might imagine, this is a very complex rule to implement. There are a number of ways that something can be protected that may happen elsewhere in the page, making the finding invalid.
> We've done our best to implement a smart rule here and will continue to refine it as we go. Currently, the logic checks general chain length (more than 3 properties in the access chain) and it IS smart enough to evaluate exclude in endpoints and render in widgets. Strategies that we have no yet covered are render in parent widgets, such as fieldSets or sections as well as page-level applicationExceptions, which are also a valid way to check ahead of time. 

---

### ScriptDescriptiveParameterRule

**Severity:** ADVICE
**Description:** Ensures array method parameters use descriptive names instead of single letters (except 'a','b' for sorting methods, which is a globally excepted rule across programming languages)
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Single-letter parameters in array methods (`x => x.active`) hide information about is being processed, making code harder to scan and understand at a glance. Descriptive names (`user => user.active`) self-document the code and prevent confusion in nested method chains where multiple single-letter variables could refer to different things.

**What it catches:**

- Single-letter parameters in array methods that make code hard to read
- Nested array methods with confusing parameter names
- Non-descriptive variable names in map, filter, find, forEach, reduce, sort

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
- **Context-aware:** Suggests `user` for `users.map()`, `team` for `teams.filter()`, etc.

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

**Severity:** ADVICE
**Description:** Ensures functions have consistent return patterns
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Functions with inconsistent returns (some code paths return a value, others return nothing) cause subtle bugs where callers receive `null` unexpectedly. This leads to null reference errors downstream or incorrect conditional logic. Ensuring all code paths explicitly return (even if it explicity `null`) makes function behavior predictable and prevents runtime errors.

**What it catches:**

- Functions with missing return statements
- Inconsistent return patterns within functions

**Example violations:**

```javascript
function processUser(user) {
    if (user.active) {
        return user.name;
    }
    // ❌ Missing return statement
}
```

**Fix:**

```javascript
function processUser(user) {
    if (user.active) {
        return user.name;
    }
    return null; // ✅ Explicit return
}
```

---

### ScriptStringConcatRule

**Severity:** ADVICE
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

**Severity:** ADVICE
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

**Severity:** ADVICE
**Description:** Detects empty function bodies
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Empty functions are usually placeholder code that was never implemented or handlers that were meant to do something but don't. They add confusion (developers wonder if they're intentional), increase code size unnecessarily, and can mask missing functionality. Either implement them or remove them to keep your codebase clean and intentional.

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

**Severity:** ADVICE
**Description:** Detects anti-pattern 'self.data = {:}' in outbound endpoint onSend scripts
**Applies to:** PMD outbound endpoint onSend scripts

**Why This Matters:**

The pattern `self.data = {:}` in onSend scripts is an anti-pattern that can cause issues with data handling in Workday Extend outbound endpoints. This pattern overwrites existing data structures and can lead to unexpected behavior or data loss. Using proper data initialization approaches ensures reliable endpoint behavior.

**What This Rule Does:**
This rule uses AST parsing to detect the anti-pattern `self.data = {:}` (assigning an empty object to self.data) in outbound endpoint onSend scripts. This pattern should be avoided as it can cause issues with data handling. Comments are automatically ignored by the parser.

**Intent:** Prevent problematic data initialization patterns in outbound endpoint scripts.

**What it catches:**

- Usage of `self.data = {:}` in outbound endpoint onSend scripts
- Anti-pattern assignments that should use alternative approaches

**Example violations:**

```
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      self.data = {:}; // ❌ Anti-pattern - avoid this
      return self.data;
    %>"
  }]
}
```

**Fix:**

```
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      // ✅ Use alternative data initialization approach
      return { /* your data here */ };
    %>"
  }]
}
```

**Note:** This rule only applies to **outbound** endpoints. Inbound endpoints are not checked. Comments containing the pattern are automatically ignored by the AST parser.

---

### ScriptUnusedFunctionRule

**Severity:** ADVICE
**Description:** Detects functions that are declared but never called in embedded script contexts
**Applies to:** PMD embedded scripts (`<% ... %>`) and Pod endpoint/widget scripts ONLY

**Why This Matters:**

Unused functions in embedded scripts add unnecessary code that developers must read and maintain, creating mental overhead when trying to understand what the page actually does. They also increase parsing time and memory usage. Removing unused functions keeps your PMD/Pod files focused and makes the actual logic easier to follow.

**What This Rule Does:**
This rule tracks function usage within embedded script contexts in PMD and Pod files. Unlike standalone `.script` files that use export patterns, embedded scripts don't have formal exports. This rule identifies function variables that are declared but never called anywhere in the script or across related script sections in the same file.

**Intent:** Identify unused helper functions in embedded scripts that can be safely removed to reduce code complexity.

**What it catches:**

- Function variables declared but never called
- Helper functions that were intended to be used but aren't referenced
- Dead code that should be removed from embedded scripts

**Example violations:**

```javascript
// In MyPage.pmd - embedded script section
<%
  var processData = function(data) {  // ✅ Used below
    return data.filter(item => item.active);
  };
  
  var unusedHelper = function(val) {  // ❌ Never called - unused function
    return val * 2;
  };
  
  var results = processData(pageVariables.items);
%>
```

**Fix:**

```javascript
// In MyPage.pmd - embedded script section
<%
  var processData = function(data) {  // ✅ Used
    return data.filter(item => item.active);
  };
  
  // ✅ Removed unusedHelper - it was never called
  
  var results = processData(pageVariables.items);
%>
```

**Note:** This rule is separate from `ScriptDeadCodeRule`, which validates export patterns in standalone `.script` files. Use `ScriptDeadCodeRule` for `.script` files and `ScriptUnusedFunctionRule` for embedded scripts in PMD/Pod files.

---

### ScriptUnusedFunctionParametersRule

**Severity:** ADVICE
**Description:** Detects unused function parameters
**Applies to:** PMD embedded scripts, Pod endpoint/widget scripts, and standalone .script files

**Why This Matters:**

Unused parameters make function signatures misleading - callers think they need to pass values that are actually ignored. This wastes developer time figuring out what to pass and creates confusion about the function's actual requirements. Removing unused parameters clarifies the API and prevents wasted effort.

**What it catches:**

- Function parameters that are declared but never used
- Parameters that could be removed to simplify the function signature

**Example violations:**

```javascript
function processUser(user, options, callback) { // ❌ options and callback unused
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

**Severity:** ADVICE
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

### ScriptUnusedScriptIncludesRule

**Severity:** ADVICE
**Description:** Detects script files that are included but never used in PMD files
**Applies to:** PMD files with script includes

**Why This Matters:**

Including unused script files forces the browser to download, parse, and load code that's never executed, directly impacting page load time. Each unnecessary include adds to your application's bundle size and slows down the initial page render. Removing unused includes makes pages load faster and reduces wasted bandwidth.

**What it catches:**

- Script files in PMD include arrays that are never called
- Dead script dependencies that increase bundle size

**Example violations:**

```javascript
// In sample.pmd
{
  "include": ["util.script", "helper.script"], // ❌ helper.script never called
  "script": "<%
    const time = util.getCurrentTime(); // Only util.script is used
  %>"
}
```

**Fix:**

```javascript
// In sample.pmd
{
  "include": ["util.script"], // ✅ Only include used scripts
  "script": "<%
    const time = util.getCurrentTime();
    const result = helper.processData(); // Or add calls to helper.script
  %>"
}
```

---

### HardcodedApplicationIdRule

**Severity:** ADVICE
**Description:** Detects hardcoded applicationId values that should be replaced with site.applicationId
**Applies to:** PMD and Pod files

**Why This Matters:**

Hardcoded application IDs break when you deploy the same code to different environments (dev, sandbox, production) because each has a unique ID. Using `site.applicationId` makes your code environment-agnostic and prevents deployment failures. This is especially critical for multi-tenant applications that need to work across different Workday instances.

**What it catches:**

- Hardcoded applicationId values in scripts and configurations
- Values that should use site.applicationId instead

**Example violations:**

```javascript
const appId = "12345"; // ❌ Hardcoded applicationId
```

**Fix:**

```javascript
const appId = site.applicationId; // ✅ Use site.applicationId
```

---

### EmbeddedImagesRule

**Severity:** ADVICE
**Description:** Detects embedded images that should be stored as external files
**Applies to:** PMD and Pod files

**Why This Matters:**

Base64-encoded images bloat your PMD/Pod file sizes dramatically (often 30% larger than the image itself) and make files harder to version control since small image changes create large text diffs. External images load asynchronously, cache better, and keep your code files focused on logic. This significantly improves page load performance and makes code reviews manageable.

**What it catches:**

- Base64 encoded images embedded directly in files
- Images that should be stored as external files

**Example violations:**

```json
{
  "type": "image",
  "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." // ❌ Embedded image
}
```

**Fix:**

```json
{
  "type": "image", 
  "src": "http://example.com/images/logo.png" // ✅ External image file
}
```

---

### HardcodedWidRule

**Severity:** ADVICE
**Description:** Detects hardcoded WID (Workday ID) values that should be configured in app attributes
**Applies to:** PMD and Pod files

**Why This Matters:**

Hardcoded WIDs (Workday IDs) are environment-specific - a worker or job WID in your sandbox won't exist in production. This causes runtime errors when the code tries to look up non-existent data. Storing WIDs in app attributes allows different values per environment and makes your application portable across tenants and instances.

**What it catches:**

- Hardcoded 32-character WID values
- WIDs that should be configured in app attributes

**Example violations:**

```javascript
const workerWid = "d9e41a8c446c11de98360015c5e6daf6"; // ❌ Hardcoded WID
```

**Fix:**

```javascript
const workerWid = appAttr.workerWid; // ✅ Use app attribute
```

---

### AMDDataProvidersWorkdayRule

**Severity:** ACTION
**Description:** Ensures AMD dataProviders don't use hardcoded *.workday.com URLs
**Applies to:** AMD application definition files

**Why This Matters:**

Hardcoded workday.com URLs in AMD dataProviders fail when deployed to different Workday environments (implementation URLs vary by tenant). Using the `apiGatewayEndpoint` variable ensures your endpoints work across all environments without code changes. Hardcoding URLs will cause complete application failure in production if not caught.

**What it catches:**

- Hardcoded *.workday.com URLs in AMD dataProviders
- URLs that should use apiGatewayEndpoint variable instead
- Both HTTP and HTTPS workday.com URLs

**Example violations:**

```json
{
  "dataProviders": [
    {
      "key": "workday-common",
      "value": "https://api.workday.com/common/v1/"  // ❌ Hardcoded workday.com URL
    },
    {
      "key": "workday-hcm", 
      "value": "https://services.workday.com/hcm/v1/"  // ❌ Hardcoded workday.com URL
    }
  ]
}
```

**Fix:**

```json
{
  "dataProviders": [
    {
      "key": "workday-app",
      "value": "<% apiGatewayEndpoint + '/apps/' + site.applicationId + '/v1/' %>"  // ✅ Use apiGatewayEndpoint
    },
    {
      "key": "workday-common",
      "value": "<% apiGatewayEndpoint + '/common/v1/' %>"  // ✅ Use apiGatewayEndpoint
    }
  ]
}
```

---

## 🏗️ Structure Rules (19 Rules)

*The Structure Rules bind the outer wards and conduits of your magical constructs. These architectural validations ensure your endpoints, widgets, and configurations form a harmonious and secure foundation for your mystical applications.*

*These rules validate widget configurations, endpoint structures, component compliance, hardcoded values, file naming conventions, and PMD organization in both PMD and Pod files.*

### EndpointFailOnStatusCodesRule

**Severity:** ACTION
**Description:** Ensures endpoints properly handle 400 and 403 error status codes
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

Without proper error handling (failOnStatusCodes), your endpoints silently swallow errors like "400 Bad Request" or "403 Forbidden", causing your application to proceed as if the call succeeded when it actually failed. This leads to data inconsistencies, broken workflows, and debugging nightmares. Explicit error handling ensures failures are properly caught and handled.

**What it catches:**

- Missing error handling for common HTTP status codes
- Endpoints that don't fail on some specific error responses

**Example violations:**

```json
{
  "endPoints": [{
    "name": "GetUser",
    "url": "/users/me"
    // ❌ Missing failOnStatusCodes
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "GetUser", 
    "url": "/users/me",
    "failOnStatusCodes": [
      {"code": "400"},
      {"code": "403"}
    ]
  }]
}
```

---

### NoIsCollectionOnEndpointsRule

**Severity:** ACTION
**Description:** Detects isCollection: true on inbound endpoints which can cause tenant-wide performance issues
**Applies to:** PMD inbound endpoints and Pod endpoints

**What it catches:**

- Inbound endpoints with `isCollection: true`
- POD endpoints with `isCollection: true`
- Does NOT check outbound endpoints (different performance characteristics)

**Why This Matters:**

Using `isCollection: true` on inbound endpoints can cause severe performance degradation affecting the entire tenant by forcing expensive database queries. This can slow down or crash the entire Workday instance for all users, not just your application. Avoiding isCollection on inbound endpoints is critical for maintaining system-wide performance and stability.

**Example violations:**

```json
{
  "inboundEndpoints": [
    {
      "name": "GetWorkers",
      "isCollection": true  // ❌ Causes tenant-wide performance issues
    }
  ],
  "outboundEndpoints": [
    {
      "name": "ProcessWorkers",
      "isCollection": true  // ✅ OK for outbound endpoints (not checked)
    }
  ]
}
```

**Fix:**

```json
{
  "inboundEndpoints": [
    {
      "name": "GetWorkers"
      // ✅ Removed isCollection or restructure to not require collections
    }
  ]
}
```

---

### OnlyMaximumEffortRule

**Severity:** ACTION
**Description:** Ensures endpoints do not use bestEffort to prevent masked API failures
**Applies to:** PMD inbound and outbound endpoints, and Pod endpoints

**What it catches:**

- Endpoints with `bestEffort: true` on inbound endpoints
- Endpoints with `bestEffort: true` on outbound endpoints
- POD endpoints with `bestEffort: true`

**Why This Matters:**

Using `bestEffort: true` on endpoints silently swallows API failures, causing your code to continue executing as if the call succeeded when it actually failed. This leads to data inconsistency, partial updates, and bugs that are extremely hard to debug because you have no visibility into the failure. Maximum effort ensures failures are properly surfaced so you can handle them explicitly.

**Example violations:**

```json
{
  "inboundEndpoints": [
    {
      "name": "GetWorkers",
      "bestEffort": true  // ❌ Can mask API failures
    }
  ],
  "outboundEndpoints": [
    {
      "name": "UpdateWorker",
      "bestEffort": true  // ❌ Can mask API failures
    }
  ]
}
```

**Fix:**

```json
{
  "inboundEndpoints": [
    {
      "name": "GetWorkers"
      // ✅ Remove bestEffort property
    }
  ],
  "outboundEndpoints": [
    {
      "name": "UpdateWorker"
      // ✅ Remove bestEffort property
    }
  ]
}
```

---

### NoPMDSessionVariablesRule

**Severity:** ACTION
**Description:** Detects outboundVariable endpoints with variableScope: session which can cause performance degradation
**Applies to:** PMD outbound endpoints only

**What it catches:**

- Outbound endpoints with `type: "outboundVariable"` AND `variableScope: "session"`
- Does NOT check inbound endpoints (only outbound)
- Does NOT check POD files (PODs don't use this pattern)

**Why This Matters:**

Session-scoped variables persist for the entire user session (potentially hours), continuously consuming memory even after the user leaves your page. This memory isn't released until logout, degrading performance over time and potentially causing out-of-memory issues for long-running sessions. Using page or task scope ensures data is cleaned up when no longer needed, keeping the application responsive.

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
      "variableScope": "page"  // ✅ Use page scope
    }
  ]
}
```

**Alternative scopes:**

- `"page"` - For page-level data (recommended for most cases)
- `"task"` - For task-level data

---

### EndpointNameLowerCamelCaseRule

**Severity:** ADVICE
**Description:** Ensures endpoint names follow lowerCamelCase convention
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

Consistent endpoint naming makes your API predictable and easier to use. LowerCamelCase is the Workday Extend standard for endpoint names, and mixing conventions creates confusion when developers try to call endpoints or debug network traffic. Following the convention improves team collaboration and makes code more professional.

**What it catches:**

- Endpoint names that don't follow camelCase naming
- Inconsistent naming conventions across endpoints

**Example violations:**

```json
{
  "endPoints": [{
    "name": "get_user_data"  // ❌ snake_case
  }, {
    "name": "GetUserProfile" // ❌ PascalCase
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getUserData"    // ✅ lowerCamelCase
  }, {
    "name": "getUserProfile" // ✅ lowerCamelCase
  }]
}
```

---

### PMDSectionOrderingRule
    "onSend": "<%
      let postData = {'name': workerName.value}; // ✅ Use a more descriptive local variable
      return postData;
    %>"
  }]
}
```

---

### EndpointBaseUrlTypeRule

**Severity:** ADVICE
**Description:** Ensures endpoint URLs don't include hardcoded *.workday.com or apiGatewayEndpoint values
**Applies to:** PMD endpoint definitions and Pod seed endpoints

**Why This Matters:**

Hardcoding workday.com URLs makes your endpoints environment-specific and breaks when deploying across different Workday instances or environments. Using `baseUrlType` (like 'workday-common' or 'workday-app') makes endpoints portable and ensures they automatically resolve to the correct URL for each environment, preventing deployment failures and simplifying configuration management.

**What it catches:**

- Hardcoded *.workday.com domains in endpoint URLs
- Hardcoded apiGatewayEndpoint values in URLs
- Endpoints that should use baseUrlType instead of hardcoded values

**Example violations:**

```json
{
  "endPoints": [{
    "name": "getWorker",
    "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getWorker",
    "url": "/workers/me",  // ✅ Relative URL
    "baseUrlType": "workday-common"  // ✅ Use baseUrlType instead
  }]
}
```

---

### PMDSectionOrderingRule

**Severity:** ADVICE (configurable)
**Description:** Ensures PMD file root-level sections follow consistent ordering for better readability
**Applies to:** PMD file structure
**Configurable:** ✅ Section order and enforcement can be customized

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
  "id": "myApp",
  "script": "<%  %>",
  "include": ["util.script"]
}
```

**Fix:**

```json
{
  "id": "myApp",           // ✅ Proper order
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

**Severity:** ACTION
**Description:** Ensures PMD pages have at least one security domain defined (excludes microConclusion and error pages unless strict mode is enabled)
**Applies to:** PMD file security configuration

**Why This Matters:**

Security domains control who can access your PMD pages in Workday. Missing security domains means your page is inaccessible to all users, causing a broken experience. Even during development, defining security domains early prevents deployment issues and ensures pages work when promoted to production. This catches a common mistake that would otherwise only surface after deployment.

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

**Example configuration:**

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

### WidgetIdRequiredRule

**Severity:** ACTION
**Description:** Ensures all widgets have an 'id' field set
**Applies to:** PMD and POD widget structures

**Why This Matters:**

Widget IDs are essential for referencing widgets in scripts (to get/set values, show/hide, etc.) and for debugging. Without IDs, you can't interact with widgets programmatically, making dynamic behavior impossible. IDs also help identify widgets in error messages and make code maintenance much easier when you need to find where a widget is defined or used.

**What it catches:**

- Widgets missing required `id` field
- Widgets that cannot be uniquely identified or referenced
- Structure validation issues that make code harder to maintain

**Smart Exclusions:**

Widget types that don't require IDs: `footer`, `item`, `group`, `title`, `pod`, `cardContainer`, `card`, and column objects (which use `columnId` instead)

**Example violations:**

```json
{
  "presentation": {
    "body": {
      "type": "richText",  // ❌ Missing id field
      "value": "Welcome"
    }
  }
}
```

**Fix:**

```json
{
  "presentation": {
    "body": {
      "type": "richText",
      "id": "welcomeMessage",  // ✅ Added id field
      "value": "Welcome"
    }
  }
}
```

---

### WidgetIdLowerCamelCaseRule

**Severity:** ADVICE
**Description:** Ensures widget IDs follow lowerCamelCase naming convention
**Applies to:** PMD and POD widget structures

**Why This Matters:**

Consistent widget ID naming makes your UI code predictable and easier to navigate. LowerCamelCase is the Workday standard, and following it means developers can guess widget names correctly when writing scripts. Mixing conventions (snake_case, PascalCase) forces constant reference checking and slows development.

**What it catches:**

- Widget IDs that don't follow lowerCamelCase convention
- Inconsistent naming across widgets
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

**Severity:** ADVICE
**Description:** Ensures footer uses pod structure (direct pod or footer with pod children)
**Applies to:** PMD file footer sections

**Why This Matters:**

Using pods for footers promotes component reuse and consistency across your application. Pods are designed to be reusable components, and structuring footers as pods makes them easier to maintain centrally and update across multiple pages. This follows Workday Extend best practices for component architecture.

**What it catches:**

- Footers that don't use pod structure
- Inconsistent footer implementations
- Missing pod widgets in footers

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
          "id": "footerPod",
          "podId": "MyFooterPod"
        }
      ]
    }
  }
}
```

---

### StringBooleanRule

**Severity:** ADVICE
**Description:** Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans
**Applies to:** PMD and POD file structures

**Why This Matters:**

String booleans (`"true"`) behave differently than actual booleans (`true`) in conditional checks - the string `"false"` is actually truthy in JavaScript, causing logic bugs. Workday Extend expects proper boolean types in widget configurations. Using string booleans can cause widgets to behave unpredictably or incorrectly (a disabled field shows as enabled).

**What it catches:**

- Boolean values represented as strings `"true"` or `"false"`
- Type inconsistencies that can cause unexpected behavior
- JSON structure violations

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

## Rule Configuration

All rules can be configured in your configuration files:

- **`configs/default.json`** - Standard configuration
- **`configs/minimal.json`** - Minimal rule set
- **`configs/comprehensive.json`** - All rules enabled with strict settings

### Configuration Options

Each rule supports:

- **`enabled`** - Enable/disable the rule
- **`severity_override`** - Override default severity (SEVERE, WARNING, INFO)
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

### FileNameLowerCamelCaseRule

**Severity:** ADVICE
**Description:** Ensures all file names follow lowerCamelCase naming convention
**Applies to:** All files (PMD, POD, AMD, SMD, Script)

**Why This Matters:**

Consistent file naming makes projects easier to navigate and prevents case-sensitivity issues when deploying across different operating systems (Windows is case-insensitive, Linux is case-sensitive). LowerCamelCase is the Workday Extend standard, and following it ensures files are organized predictably and reduces confusion in team environments.

**What it catches:**

- Files using PascalCase (e.g., `MyPage.pmd`)
- Files using snake_case (e.g., `my_page.pmd`)
- Files using UPPERCASE (e.g., `MYPAGE.pmd`)
- Files starting with numbers (e.g., `2myPage.pmd`)

**Valid naming patterns:**

- **Pure lowerCamelCase**: `myPage.pmd`, `helperFunctions.script`
- **App ID format**: `myApp_abcdef.amd`, `template_nkhlsq.smd` (name_postfix where postfix is 6 lowercase letters)

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
myApp_abcdef.amd        // ✅ App ID format
template_nkhlsq.smd     // ✅ App ID format
```

**Fix:**

Rename files to follow lowerCamelCase convention. For app-level files (AMD, SMD), the app ID format `name_postfix` is allowed.

---

### MultipleStringInterpolatorsRule

**Severity:** ADVICE
**Description:** Detects multiple string interpolators in a single string which should use template literals instead
**Applies to:** PMD and POD files

**What it catches:**

- Strings with 2 or more `<% %>` interpolators
- String values that mix static text with multiple dynamic values
- Does NOT flag strings already using template literals (backticks with `${}`)

**Why This Matters:**

Multiple interpolators (`<% name %> and <% age %>`) create multiple parse operations and are harder to read than a single template literal. Each interpolator adds overhead, and mixing static text with scattered dynamic values makes the string's structure unclear. Using one interpolator with a template literal (`<% \`Name: ${name}, Age: ${age}\` %>`) is cleaner, more performant, and easier to maintain.

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
  "value": "<% `My name is ${name} and I like ${food}` %>"  // ✅ SINGLE interpolator with template literal
}

{
  "label": "<% `Name: ${firstName}, Age: ${age}, City: ${city}` %>"  // ✅ SINGLE interpolator with template literal
}
```

**Note:** Use ONE `<% %>` interpolator containing a template literal with backticks (\`) and `${}` for variables.

---

### GridPagingWithSortableFilterableRule

**Severity:** ACTION
**Description:** Detects grids with paging and sortableAndFilterable columns which can cause performance issues
**Applies to:** PMD and POD grid widgets

**Why This Matters:**

Combining paging with sortableAndFilterable columns forces Workday to load and process the entire dataset client-side for sorting/filtering, defeating the purpose of paging. This can cause severe performance degradation with large datasets, freezing the browser or timing out. Either disable paging or remove sortableAndFilterable to prevent performance issues.

**What it catches:**

- Grid widgets with `autoPaging: true` OR `pagingInfo` present
- AND any column with `sortableAndFilterable: true`
- Checks nested grids in sections and other containers

**Why it matters:**

Combining paging with sortable/filterable columns can cause severe performance degradation due to how data is fetched and processed. This can lead to slow page loads and poor user experience.

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

**Recommendation:** For large datasets, use paging without sortableAndFilterable. For small datasets, use sortableAndFilterable without paging.

---

## 📊 Quick Reference

| Rule Name                                      | Category  | Severity  | Default Enabled | Key Settings       |
| ---------------------------------------------- | --------- | --------- | --------------- | ------------------ |
| **ScriptVarUsageRule**                   | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptDeadCodeRule**                   | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptComplexityRule**                 | Script    | 🟢 ADVICE | ✅              | `max_complexity` |
| **ScriptLongFunctionRule**               | Script    | 🟢 ADVICE | ✅              | `max_length`     |
| **ScriptFunctionParameterCountRule**     | Script    | 🟢 ADVICE | ✅              | `max_parameters` |
| **ScriptFunctionParameterNamingRule**    | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptUnusedVariableRule**             | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptUnusedFunctionParametersRule**   | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptVariableNamingRule**             | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptConsoleLogRule**                 | Script    | 🔴 ACTION | ✅              | —                 |
| **ScriptNullSafetyRule**                 | Script    | 🔴 ACTION | ✅              | —                 |
| **ScriptEmptyFunctionRule**              | Script    | 🔴 ACTION | ✅              | —                 |
| **ScriptNestingLevelRule**               | Script    | 🟢 ADVICE | ✅              | `max_nesting`    |
| **ScriptLongScriptBlockRule**            | Script    | 🟢 ADVICE | ✅              | `max_length`     |
| **ScriptMagicNumberRule**                | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptStringConcatRule**               | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptArrayMethodUsageRule**           | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptDescriptiveParametersRule**      | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptFunctionReturnConsistencyRule**  | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptVerboseBooleanRule**             | Script    | 🟢 ADVICE | ✅              | —                 |
| **StringBooleanRule**                    | Script    | 🟢 ADVICE | ✅              | —                 |
| **UnusedScriptIncludesRule**             | Script    | 🟢 ADVICE | ✅              | —                 |
| **ScriptOnSendSelfDataRule**             | Script    | 🟢 ADVICE | ✅              | —                 |
| **EndpointFailOnStatusCodesRule**        | Structure | 🔴 ACTION | ✅              | —                 |
| **EndpointNameLowerCamelCaseRule**       | Structure | 🟢 ADVICE | ✅              | —                 |
| **EndpointBaseUrlTypeRule**              | Structure | 🟢 ADVICE | ✅              | —                 |
| **WidgetIdRequiredRule**                 | Structure | 🔴 ACTION | ✅              | —                 |
| **WidgetIdLowerCamelCaseRule**           | Structure | 🟢 ADVICE | ✅              | —                 |
| **HardcodedApplicationIdRule**           | Structure | 🟢 ADVICE | ✅              | —                 |
| **HardcodedWidRule**                     | Structure | 🟢 ADVICE | ✅              | —                 |
| **ReadableEndpointPathsRule**            | Structure | 🟢 ADVICE | ✅              | —                 |
| **PMDSectionOrderingRule**               | Structure | 🟢 ADVICE | ✅              | `required_order` |
| **PMDSecurityDomainRule**                | Structure | 🔴 ACTION | ✅              | `strict`         |
| **EmbeddedImagesRule**                   | Structure | 🟢 ADVICE | ✅              | —                 |
| **FooterPodHubMicroExclusionsRule**      | Structure | 🟢 ADVICE | ✅              | —                 |
| **AmdDataProvidersWorkdayRule**          | Structure | 🟢 ADVICE | ✅              | —                 |
| **FileNameLowerCamelCaseRule**           | Structure | 🟢 ADVICE | ✅              | —                 |
| **NoIsCollectionOnEndpointsRule**        | Structure | 🔴 ACTION | ✅              | —                 |
| **OnlyMaximumEffortRule**                | Structure | 🔴 ACTION | ✅              | —                 |
| **NoPMDSessionVariablesRule**            | Structure | 🔴 ACTION | ✅              | —                 |
| **MultipleStringInterpolatorsRule**      | Structure | 🟢 ADVICE | ✅              | —                 |
| **GridPagingWithSortableFilterableRule** | Structure | 🔴 ACTION | ✅              | —                 |

---

## Summary

The Arcane Auditor channels mystical powers through **42 rules** across **2 categories**:

- ✅ **23 Script Rules** - Code quality for PMD and standalone scripts
- ✅ **19 Structure Rules** - Widget configurations, endpoint validation, structural compliance, hardcoded values, and PMD organization

**Severity Distribution:**

- **10 ACTION Rules**: Critical issues requiring immediate attention
- **32 ADVICE Rules**: Recommendations for code quality and best practices

These rules help maintain consistent, high-quality Workday Extend applications by catching issues that compilers aren't designed to catch, but are important for maintainability, performance, and team collaboration.
