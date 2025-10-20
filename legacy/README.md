# Legacy Archive

This directory contains archived code generators and coordination scripts that were used during the development of ChatterFix Enterprise CMMS.

## Archive Structure

### `/architecture_generators/`
Contains large standalone Python files that were used to generate code templates, deployment configurations, and documentation. These generators served their purpose and the output has been integrated into the main codebase.

**Archived Files:**
- `enterprise_frontend_architecture.py` - React frontend template generator
- `enterprise_backend_security.py` - Microservices security template generator  
- `enterprise_database_analytics.py` - Database schema and analytics generator
- `enterprise_deployment_orchestrator.py` - Kubernetes deployment manifest generator
- `enterprise_monitor.py` - Monitoring service template generator
- `predictive_architecture_diagram.py` - Architecture documentation generator
- `predictive_deployment_automation.py` - Deployment automation generator

### `/coordination_scripts/`
Contains one-time coordination and orchestration scripts used during development.

**Archived Files:**
- `ai_team_enterprise_meeting.py` - AI team coordination script

## Why These Files Were Archived

1. **Code Generators**: These files generated templates and configurations that have been integrated into the main codebase. They served their purpose and are no longer needed for runtime operation.

2. **Duplication**: Many of these generators created functionality that overlapped with existing services in `core/cmms/`.

3. **Large Size**: Combined, these generators contained 5,107 lines of code that were primarily for scaffolding rather than production functionality.

4. **Maintenance Burden**: Keeping large generator files alongside production code creates confusion and maintenance overhead.

## What Was Preserved

- **Useful SQL Schemas**: Extracted to `core/cmms/database/schemas/`
- **Production Services**: Moved to `core/cmms/services/`
- **Documentation Artifacts**: Architecture diagrams and documentation remain in main directory
- **Deployment Configs**: Useful Kubernetes manifests preserved in `core/cmms/k8s/`

## Recovery

If any of these generators are needed again, they can be restored from this archive. However, the recommended approach is to use the organized services and extracted components rather than regenerating code.

**Archive Date**: 2025-10-19  
**Audited By**: ChatterFix Enterprise QA Engineer