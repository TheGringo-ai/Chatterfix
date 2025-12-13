# Quick Fix Workflow

Apply common fixes based on learned patterns from CLAUDE.md.

## Known Issue Patterns

### 1. DateTime JSON Serialization Error
**Symptom**: 500 error with "Object of type datetime is not JSON serializable"
**Fix**: Convert datetime objects using `.strftime("%Y-%m-%d %H:%M")`

```python
# Before (broken)
return {"created_at": datetime.now()}

# After (fixed)
return {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
```

### 2. Dark Mode Toggle Not Working
**Symptom**: Theme toggle doesn't persist or apply
**Fix**: Apply dark-mode class to BOTH document elements

```javascript
// Ensure both are set
document.documentElement.classList.toggle('dark-mode');
document.body.classList.toggle('dark-mode');
```

### 3. HTTP 405 on Root Domain
**Symptom**: chatterfix.com returns 405 error
**Fix**: Add root route with redirect

```python
@app.get("/", tags=["Core"])
async def root():
    return RedirectResponse(url="/demo", status_code=302)
```

### 4. Firebase Connection Failure
**Symptom**: Firestore operations fail silently
**Fix**: Add proper fallback data

```python
try:
    data = await firebase_client.get_document(...)
except Exception as e:
    logger.error(f"Firebase error: {e}")
    data = get_fallback_demo_data()
```

### 5. Local vs Production Gap
**Symptom**: Works locally, fails in production
**Fix**:
1. Commit ALL changes before deploying
2. Check environment variables match
3. Verify file paths are relative

## Diagnostic Commands

```bash
# Check for uncommitted changes
git status

# View recent changes
git diff HEAD~1

# Check Docker logs
docker logs chatterfix --tail 50

# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=20
```

## Apply Fix Pattern

1. Identify the symptom
2. Match to known pattern above
3. Apply the fix
4. Test locally
5. Commit and deploy
6. Verify in production

## When Pattern Not Found

If the issue doesn't match known patterns:
1. Document the new issue
2. Find and apply fix
3. Add pattern to CLAUDE.md for future reference
4. Update AI team memory system
