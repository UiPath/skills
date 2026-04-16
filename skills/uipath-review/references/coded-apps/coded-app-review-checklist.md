# Coded App Review Checklist

Quality checklist for UiPath Coded Web Applications — apps built with web frameworks (React, Angular, Vue, etc.) and deployed through the UiPath platform.

> **Unit of Work:** Before running the technical checks below, complete Step 3a (Unit of Work Discovery) from SKILL.md. For coded apps the declared unit is the entry point input schema (`operate.json` / `entry-points.json`). The actual unit is what each endpoint/page action produces. If a single user action triggers N unbounded downstream calls over a sub-collection of input, that is a Granularity Mismatch (see [rpa-common-issues.md](../rpa/rpa-common-issues.md) for the generic pattern).

## 1. Project Structure

### Required Files

| Check | Severity | How to Verify |
|---|---|---|
| `package.json` exists | Critical | `ls package.json` |
| `.uipath/` directory exists (project metadata) | Critical | `ls -d .uipath/` |
| `app.config.json` exists (after first publish) | Info | `ls app.config.json` |
| Build output directory exists (`dist/` or equivalent) | Warning | `ls dist/` |
| `operate.json` present | Info | `ls operate.json` |
| `bindings.json` present (if using UiPath resources) | Warning | `ls bindings.json` |
| `entry-points.json` present | Warning | `ls entry-points.json` |
| `package-descriptor.json` present | Info | `ls package-descriptor.json` |

### package.json Quality

| Check | Severity | How to Verify |
|---|---|---|
| `name` field is set and valid | Warning | Read package.json |
| `version` field is set | Warning | Read package.json |
| Build script defined (`scripts.build`) | Critical | Read package.json |
| Dependencies properly declared (not all in devDependencies or vice versa) | Info | Review dependency sections |
| No unnecessary dependencies | Info | Review dependency list |
| Lock file exists (`package-lock.json` or `yarn.lock`) | Warning | Check for lock file |

## 2. Build Verification

| Check | Severity | How to Verify |
|---|---|---|
| `npm run build` completes successfully | Critical | Run build command |
| `dist/` (or configured output) contains expected files | Critical | `ls dist/` |
| Build output includes an `index.html` entry point | Critical | `ls dist/index.html` |
| No build warnings about missing dependencies | Warning | Check build output |
| Bundle size is reasonable (no massive unoptimized bundles) | Info | Check dist/ file sizes |

## 3. Pack Readiness

| Check | Severity | How to Verify |
|---|---|---|
| Dry-run pack succeeds | Critical | `uip codedapp pack dist --dry-run` |
| `.uipath/` metadata is consistent with package.json | Warning | Compare versions and names |
| No sensitive files included in build output | Critical | Check dist/ for .env, credentials, etc. |
| No source maps in production build (security risk) | Warning | Check for `.map` files in dist/ |

## 4. Performance

### Page Complexity Limits

| Limit | Maximum | Severity if Exceeded |
|---|---|---|
| Controls per page | 200 | Warning |
| Complex controls per page (tables, grids) | 5 | Warning |
| Tabs per Tab control | 10 | Warning |
| Nested containers | 5 levels | Warning |
| Nested rules in an event | 10 | Warning |
| Read-only records in Table controls | 200 | Warning |

### Asset Optimization

| Check | Severity | How to Verify |
|---|---|---|
| Images optimized (not full-resolution for thumbnails) | Info | Check image file sizes |
| Image sizes >50% of original dimensions | Info | Check resize ratios |
| Video uses embed links, not direct file hosting | Info | Check for video elements |
| No unnecessary large assets in build output | Warning | Check dist/ file sizes |

## 5. Security

| Check | Severity | How to Verify |
|---|---|---|
| No hardcoded API keys, tokens, or secrets | Critical | Grep for `apiKey`, `secret`, `token`, `password` in source |
| No `.env` file included in build output | Critical | `ls dist/.env` |
| No source maps in production (`*.map` files) | Warning | `find dist/ -name "*.map"` |
| Authentication properly configured | Warning | Check auth patterns |
| API calls use HTTPS (not HTTP) | Warning | Grep for `http://` in source |
| No sensitive data in client-side storage (localStorage, cookies) | Warning | Check storage usage patterns |
| Content Security Policy configured | Info | Check meta tags or headers |
| No known vulnerable dependencies | Warning | `npm audit` |

## 6. Code Quality

| Check | Severity | How to Verify |
|---|---|---|
| Consistent framework usage (not mixing React/Angular/Vue patterns) | Warning | Review imports and component patterns |
| Component modularity (no god components with 500+ lines) | Warning | Check file sizes |
| Error boundaries implemented (React) or error handlers (Angular/Vue) | Warning | Check error handling patterns |
| Loading states handled for async operations | Info | Check for loading indicators |
| Form validation present for user inputs | Warning | Check form handling |
| Accessibility basics (alt text, ARIA labels, keyboard navigation) | Info | Check for a11y attributes |
| No TODO/FIXME/HACK comments in production code | Info | Grep for TODO, FIXME, HACK |
| Consistent code style (linting configured) | Info | Check for `.eslintrc` or equivalent |

## 7. UiPath Integration

| Check | Severity | How to Verify |
|---|---|---|
| Bindings correctly reference UiPath resources | Warning | Read bindings.json |
| Process invocations use correct process names/versions | Warning | Verify referenced processes |
| Connection references are valid | Warning | Check connection configs |
| Error handling for UiPath API calls | Warning | Check error handling patterns |

## 8. Deployment Configuration

| Check | Severity | How to Verify |
|---|---|---|
| App type correctly set (Web App / Action App) | Warning | Check app.config.json |
| Version management in place | Warning | Check version fields |
| Environment-specific configuration externalized | Warning | No hardcoded env-specific URLs |
| Deployment target correctly configured | Warning | Check deploy config |

## 9. Deployment Lifecycle Verification

The complete deployment lifecycle:

```
1. Build: npm run build → dist/
2. Pack:  uip codedapp pack dist → .uipath/*.nupkg
3. Publish: uip codedapp publish → registers with Apps service
4. Deploy: uip codedapp deploy → deploys to UiPath platform
```

| Check | Severity | How to Verify |
|---|---|---|
| Full lifecycle completes without errors | Critical | Run each step |
| Published version matches expected version | Warning | Check version after publish |
| App accessible after deployment | Critical | Verify app URL |
| Upgrade path works (not just fresh deploy) | Info | Test upgrade scenario |
