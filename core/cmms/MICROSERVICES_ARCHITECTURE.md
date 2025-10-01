# ChatterFix CMMS - Microservices Architecture

## Overview

The ChatterFix CMMS system has been refactored from a monolithic architecture to a microservices architecture to resolve Cloud Run deployment issues and improve scalability. The system now consists of two main services:

1. **Database Service** - Dedicated database operations microservice
2. **Main Application** - UI and business logic service

## Architecture Diagram

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│                 │◄──────────────────► │                 │
│  Main           │                     │  Database       │
│  Application    │                     │  Service        │
│  (Port 8080)    │                     │  (Port 8081)    │
│                 │                     │                 │
└─────────────────┘                     └─────────────────┘
         │                                       │
         │                                       │
    ┌────▼────┐                             ┌───▼───┐
    │   UI    │                             │ DB    │
    │ Static  │                             │(PG/   │
    │ Files   │                             │SQLite)│
    └─────────┘                             └───────┘
```

## Services

### Database Service (`database_service.py`)

**Purpose**: Dedicated microservice for all database operations using the SimpleDatabaseManager.

**Features**:
- RESTful API for all database operations
- Health checks and monitoring
- Support for both PostgreSQL and SQLite
- Optimized for Cloud Run deployment
- Built-in error handling and retry logic

**Key Endpoints**:
- `GET /health` - Service health check
- `POST /api/query` - Generic query execution
- `GET /api/work-orders` - Get work orders
- `POST /api/work-orders` - Create work order
- `GET /api/assets` - Get assets
- `POST /api/assets` - Create asset
- `GET /api/users` - Get users
- `GET /api/parts` - Get parts
- `GET /api/stats/overview` - Get statistics

**Configuration**:
- Port: 8080 (8081 in local development)
- Memory: 1Gi
- CPU: 1
- Environment Variables:
  - `DATABASE_URL` - PostgreSQL connection string
  - `ENVIRONMENT` - production/development

### Main Application (`app_microservice.py`)

**Purpose**: Handles UI, business logic, and proxies requests to the database service.

**Features**:
- Clean web interface using Bootstrap
- API endpoints that proxy to database service
- Authentication and authorization (JWT)
- Static file serving
- Error handling with fallback UI

**Key Endpoints**:
- `GET /` - Dashboard
- `GET /workorders` - Work orders page
- `GET /assets` - Assets page
- `GET /parts` - Parts page
- `GET /health` - Application health check
- `GET /api/*` - API endpoints (proxy to database service)

**Configuration**:
- Port: 8080
- Memory: 2Gi
- CPU: 2
- Environment Variables:
  - `DATABASE_SERVICE_URL` - URL of database service
  - `JWT_SECRET` - JWT signing secret
  - `ENVIRONMENT` - production/development

## Database Client (`database_client.py`)

The database client provides a clean interface for the main application to communicate with the database service via HTTP.

**Features**:
- Automatic service discovery
- Connection pooling via httpx
- Error handling and retries
- Synchronous wrapper for async operations
- Backward compatibility with existing code

## Deployment

### Cloud Run Deployment

The system includes three deployment scripts:

1. **`deploy-database-service.sh`** - Deploys database service
2. **`deploy-main-app.sh`** - Deploys main application
3. **`deploy-microservices.sh`** - Deploys both services in sequence

**Deployment Process**:
```bash
# Deploy both services
./deploy-microservices.sh

# Or deploy individually
./deploy-database-service.sh
./deploy-main-app.sh
```

### Local Development

For local testing, use Docker Compose:

```bash
# Build and run locally
docker-compose up --build

# Test the deployment
./test-microservices.sh

# Access the application
# Main app: http://localhost:8080
# Database service: http://localhost:8081
```

## Configuration Management

### Environment Variables

**Database Service**:
- `DATABASE_URL` - PostgreSQL connection string
- `ENVIRONMENT` - production/development
- `PORT` - Service port (default: 8080)

**Main Application**:
- `DATABASE_SERVICE_URL` - Database service URL
- `JWT_SECRET` - JWT signing secret
- `ENVIRONMENT` - production/development
- `DOMAIN` - Application domain
- `PORT` - Service port (default: 8080)

### Service Discovery

The main application automatically discovers the database service URL using:
1. Environment variable `DATABASE_SERVICE_URL`
2. Auto-generated URL based on Cloud Run naming conventions
3. Default to localhost for development

## Benefits of Microservices Architecture

### Resolved Issues
1. **Cloud Run 503 Errors**: Reduced complexity eliminates startup timeouts
2. **Dependency Management**: Separated heavy database dependencies
3. **Scalability**: Services can scale independently
4. **Maintainability**: Clear separation of concerns

### Performance Improvements
1. **Faster Deployments**: Smaller, focused services deploy faster
2. **Resource Optimization**: Each service uses only needed resources
3. **Fault Isolation**: Database issues don't crash the UI
4. **Independent Scaling**: Scale database operations separately from UI

### Development Benefits
1. **Team Productivity**: Teams can work on services independently
2. **Technology Flexibility**: Different services can use different technologies
3. **Testing**: Easier to test individual components
4. **Debugging**: Isolated logs and metrics per service

## Monitoring and Health Checks

Both services include comprehensive health checks:

### Database Service Health
- Database connectivity
- Table existence
- Query execution test
- Connection pool status

### Main Application Health
- Service availability
- Database service connectivity
- External dependency status

## Security

### Service-to-Service Communication
- Internal Cloud Run networking
- No external authentication between services
- Network-level isolation

### User Authentication
- JWT-based authentication
- Secure token handling
- Role-based access control (planned)

## File Structure

```
core/cmms/
├── database_service.py          # Database microservice
├── app_microservice.py          # Main application
├── database_client.py           # HTTP client for database service
├── simple_database_manager.py   # Core database manager
├── Dockerfile.database          # Database service Docker image
├── Dockerfile.app               # Main app Docker image
├── docker-compose.yml           # Local development setup
├── deploy-database-service.sh   # Database service deployment
├── deploy-main-app.sh           # Main app deployment
├── deploy-microservices.sh      # Complete deployment
├── test-microservices.sh        # Testing script
├── database_service_requirements.txt  # Database service dependencies
├── app_microservice_requirements.txt  # Main app dependencies
└── MICROSERVICES_ARCHITECTURE.md     # This documentation
```

## Migration from Monolithic Architecture

### What Changed
1. **Database Operations**: Moved from direct database calls to HTTP API calls
2. **Dependencies**: Split heavy dependencies between services
3. **Deployment**: Two separate Cloud Run services instead of one
4. **Configuration**: Service discovery and inter-service communication

### Backward Compatibility
The database client provides the same interface as the original database manager, making the migration seamless for existing code.

## Troubleshooting

### Common Issues

1. **Service Discovery Failures**
   - Check `DATABASE_SERVICE_URL` environment variable
   - Verify database service is running and accessible

2. **Database Connection Issues**
   - Check database service health endpoint
   - Verify PostgreSQL connection string
   - Check Cloud Run service permissions

3. **Deployment Failures**
   - Ensure gcloud CLI is authenticated
   - Check project permissions
   - Verify Docker images build successfully

### Debugging

```bash
# Check service logs
gcloud logs tail --service=chatterfix-cmms
gcloud logs tail --service=chatterfix-database

# Test service connectivity
curl https://chatterfix-database-[region]-[project].a.run.app/health
curl https://chatterfix-cmms-[region]-[project].a.run.app/health

# Local debugging
docker-compose logs database-service
docker-compose logs main-app
```

## Future Enhancements

1. **Service Mesh**: Implement Istio for advanced traffic management
2. **Message Queues**: Add async processing with Cloud Pub/Sub
3. **Caching Layer**: Add Redis for improved performance
4. **API Gateway**: Centralized API management and authentication
5. **Observability**: Enhanced monitoring with Cloud Trace and Cloud Profiler