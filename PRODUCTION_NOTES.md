# Production Notes

Maintenance log for ChatterFix production system.

---

## 2026-01-28 — Security Hardening

**Commits:** `990e466c`, `b2b5495b`, `d39879c5`, `8874e32e`

### Backend Security Fixes
- **Auth timeout handling**: Added 5-second async timeout to Firebase token verification to prevent hangs
- **Specific exception handling**: Replaced broad `except Exception` with `InvalidIdTokenError`, `ExpiredIdTokenError`, `RevokedIdTokenError`
- **Security logging**: Added logging for failed authentication attempts with client IP
- **Configurable roles**: Replaced hardcoded "manager" with `ADMIN_ROLES` set

### Dependency Updates
- **bleach → nh3**: Migrated from deprecated bleach library to nh3 (Rust-based, actively maintained)
- **python-multipart**: Updated to 0.0.22 (CVE-2026-24486)
- **async-storage**: Updated to 2.2.0 for firebase@12.8.0 compatibility

### Mobile
- Fixed npm audit vulnerabilities (lodash prototype pollution)
- Resolved async-storage version conflict with firebase

### Deferred
- Expo SDK 50 → 54 upgrade (breaking change, requires separate migration)

**Result:** Production deployed, all systems healthy.

---

## Decisions Log

| Decision | Reason | Date |
|----------|--------|------|
| Use nh3 over bleach | bleach deprecated, nh3 is Rust-based and maintained | 2026-01-28 |
| 5-second auth timeout | Prevent Firebase hangs in production | 2026-01-28 |
| Specific Firebase exceptions | Better error handling and security logging | 2026-01-28 |
| Defer Expo 54 upgrade | Breaking change, not urgent for dev builds | 2026-01-28 |
| async-storage 2.x | Required by firebase@12.8.0 | 2026-01-28 |

---

## Production URLs

- **Web:** https://chatterfix.com
- **API Docs:** https://chatterfix.com/docs
- **Health:** https://chatterfix.com/health

---

## Deployment

- **Platform:** Google Cloud Run
- **Region:** us-central1
- **CI/CD:** GitHub Actions (push to main triggers deploy)
- **Project:** fredfix

---

## Contact

For production issues: Check GitHub Actions logs first, then Cloud Run logs.
