# AI-Powered Code Review

Perform comprehensive code review using the AI team collaboration framework.

## Review Scope

Analyze the following for the current changes:

1. **Security Analysis**
   - Check for OWASP Top 10 vulnerabilities
   - SQL injection, XSS, command injection risks
   - Sensitive data exposure
   - Authentication/authorization issues

2. **Code Quality**
   - Code complexity and maintainability
   - DRY principle violations
   - Proper error handling
   - Type safety and validation

3. **Performance**
   - Database query optimization
   - Memory leaks or inefficiencies
   - Unnecessary API calls
   - Caching opportunities

4. **ChatterFix Patterns**
   - Follows technician-first design
   - Proper JSON serialization (datetime handling)
   - Firebase/Firestore best practices
   - Voice command compatibility

## Execution

1. Get the diff of staged changes:
   ```bash
   git diff --staged
   ```

2. If no staged changes, get recent uncommitted changes:
   ```bash
   git diff
   ```

3. Analyze against learned lessons from CLAUDE.md:
   - DateTime JSON serialization (use .strftime())
   - Dark mode toggle functionality
   - Root route presence for domain mapping
   - Proper fallback data for Firebase failures

4. Check against known mistake patterns in the AI team memory system.

## Output

Provide a structured review with:
- **Critical Issues**: Must fix before merge
- **Warnings**: Should consider fixing
- **Suggestions**: Nice-to-have improvements
- **Patterns Detected**: Known issues from mistake database
