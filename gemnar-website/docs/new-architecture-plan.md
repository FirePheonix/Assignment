# New Architecture Plan: Controller Node with Auto-Scaling Workers

## Overview

This document outlines the migration from a single-server deployment to a controller-worker architecture using Vultr VPS instances, where the controller node serves as the database server, load balancer, and static/media file server, while worker nodes can be dynamically scaled based on memory usage.

## Current State Analysis

**Current Architecture:**
- Single Vultr VPS running Django application
- PostgreSQL database on same server
- Nginx serving as reverse proxy and static file server
- Uvicorn application server
- Ansible-based deployment

**Current Components:**
- Django application with channels for WebSocket support
- PostgreSQL database
- Redis for caching/sessions
- Static files served by Nginx
- Media files served by Nginx
- SSL termination at Nginx

## Proposed Architecture

### Controller Node (Primary)
**Role:** Central coordinator, database server, load balancer, static/media server
**Vultr VPS Requirements:** 4-8 CPU cores, 16-32GB RAM, 200GB+ SSD

**Services:**
- PostgreSQL database (primary)
- Nginx (load balancer + static/media server)
- Redis (shared cache/sessions)
- Auto-scaling manager daemon
- Health check monitoring
- SSL termination
- Backup services

### Worker Nodes (Auto-Scalable)
**Role:** Django application processing
**Vultr VPS Requirements:** 2-4 CPU cores, 8-16GB RAM, 50GB SSD

**Services:**
- Django application (Uvicorn)
- Minimal Nginx (health check endpoint only)
- Monitoring agent

## Detailed Component Design

### 1. Controller Node Configuration

#### Database Setup
- PostgreSQL as primary database server
- Configure for remote connections from worker nodes
- Implement connection pooling (PgBouncer)
- Database-backed sessions for cross-node session sharing
- Regular automated backups

#### Load Balancer (Nginx)
```nginx
upstream django_workers {
    # Workers will be dynamically added/removed
    server worker1.internal:8000 max_fails=3 fail_timeout=30s;
    server worker2.internal:8000 max_fails=3 fail_timeout=30s;
    # Additional workers added dynamically
}

server {
    listen 443 ssl http2;
    server_name gemnar.com www.gemnar.com;
    
    # Static and media files served directly
    location /static/ {
        alias /var/www/static/;
        expires 1y;
    }
    
    location /media/ {
        alias /var/www/media/;
        expires 1d;
    }
    
    # Application requests to workers
    location / {
        proxy_pass http://django_workers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://django_workers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### Auto-Scaling Manager
- Python daemon monitoring worker node memory usage
- Integration with Vultr API for instance creation/deletion
- Memory threshold configuration (scale up >80%, scale down <30%)
- Minimum/maximum worker count limits
- Graceful worker shutdown procedures

#### Health Check System
- HTTP health check endpoint on each worker
- Database connectivity check
- Memory/CPU threshold monitoring
- Failed worker automatic removal from load balancer

### 2. Worker Node Configuration

#### Django Application
- Stateless Django application
- Database connections to controller node
- Redis connections to controller node for caching
- No local file storage (all media on controller)
- Health check endpoint at `/health/`

#### Health Check Endpoint
```python
# In Django views
def health_check(request):
    """Health check endpoint for load balancer"""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'memory': check_memory_usage(),
        'disk': check_disk_space()
    }
    
    if all(checks.values()):
        return JsonResponse({'status': 'healthy', 'checks': checks})
    else:
        return JsonResponse({'status': 'unhealthy', 'checks': checks}, status=503)
```

### 3. Network Architecture

#### Private Network Setup
- Vultr private networking between controller and workers
- Controller: 10.0.0.1
- Workers: 10.0.0.10-10.0.0.100
- Database connections over private network
- Redis connections over private network

#### Security Configuration
- Controller node: Public access on ports 80, 443, 22
- Worker nodes: Private network only, no public access except SSH
- Database firewall rules restricting access to worker subnet
- SSL certificates managed on controller node only

### 4. Auto-Scaling Implementation

#### Memory-Based Scaling Rules
```yaml
scaling_config:
  memory_threshold_scale_up: 80%      # Scale up when worker memory > 80%
  memory_threshold_scale_down: 30%    # Scale down when worker memory < 30%
  min_workers: 2                      # Always maintain minimum workers
  max_workers: 10                     # Maximum worker instances
  cooldown_scale_up: 300s             # Wait 5 min before scaling up again
  cooldown_scale_down: 600s           # Wait 10 min before scaling down
  evaluation_periods: 3               # Check 3 consecutive periods
```

#### Vultr API Integration
- Automated worker instance creation using Vultr API
- Custom cloud-init scripts for worker initialization
- Automatic DNS/network configuration
- Graceful instance termination

### 5. Session Management

#### Database-Backed Sessions
```python
# Django settings for shared sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

#### Redis Configuration
- Shared Redis instance on controller node
- Used for caching, not sessions (for reliability)
- Worker nodes connect to controller Redis
- Configurable fallback if Redis unavailable

### 6. Deployment Strategy

#### Phase 1: Controller Node Setup
1. Migrate current server to controller role
2. Configure PostgreSQL for remote connections
3. Set up Redis for shared caching
4. Implement health check monitoring
5. Create auto-scaling manager daemon

#### Phase 2: Worker Node Template
1. Create worker node Ansible playbook
2. Implement stateless Django configuration
3. Set up health check endpoints
4. Test worker connectivity to controller

#### Phase 3: Load Balancer Configuration
1. Configure Nginx upstream with initial workers
2. Implement dynamic upstream management
3. Test load distribution and failover
4. Validate session sharing across workers

#### Phase 4: Auto-Scaling Implementation
1. Develop Vultr API integration
2. Implement memory monitoring and scaling logic
3. Create worker provisioning automation
4. Test scaling up and down scenarios

### 7. Monitoring and Maintenance

#### Monitoring Stack
- Controller node resource monitoring
- Worker node memory/CPU tracking
- Database performance monitoring
- Load balancer metrics
- Application-level metrics via Django

#### Backup Strategy
- PostgreSQL automated backups (daily)
- Static/media file backups
- Configuration backups
- Cross-region backup storage

#### Maintenance Procedures
- Rolling worker updates with zero downtime
- Controller node maintenance windows
- Database maintenance and optimization
- Security patch management

## Migration Steps

### Step 1: Controller Node Preparation
- [ ] Configure PostgreSQL for remote connections
- [ ] Install and configure Redis
- [ ] Set up shared static/media directories
- [ ] Implement health check monitoring system
- [ ] Create auto-scaling manager service

### Step 2: Worker Node Template Creation
- [ ] Create Ansible playbook for worker deployment
- [ ] Configure stateless Django settings
- [ ] Implement health check endpoint
- [ ] Test database connectivity from worker

### Step 3: Load Balancer Setup
- [ ] Configure Nginx upstream configuration
- [ ] Implement dynamic upstream management
- [ ] Set up SSL termination on controller
- [ ] Test load distribution

### Step 4: Auto-Scaling Implementation
- [ ] Develop Vultr API integration module
- [ ] Create memory monitoring daemon
- [ ] Implement scaling decision logic
- [ ] Test auto-scaling scenarios

### Step 5: Production Migration
- [ ] Deploy initial worker nodes
- [ ] Migrate traffic to new architecture
- [ ] Monitor system performance
- [ ] Fine-tune scaling parameters

## Configuration Files Structure

```
ansible/
├── controller-playbook.yml          # Controller node setup
├── worker-playbook.yml              # Worker node template
├── templates/
│   ├── nginx-controller.conf.j2     # Controller Nginx config
│   ├── nginx-worker.conf.j2         # Worker Nginx config
│   ├── postgresql.conf.j2           # PostgreSQL config
│   └── redis.conf.j2                # Redis config
├── scripts/
│   ├── autoscaler.py                # Auto-scaling daemon
│   ├── health-monitor.py            # Health monitoring
│   └── worker-provision.py          # Worker provisioning
└── inventory/
    ├── controller.ini               # Controller inventory
    └── workers.ini                  # Worker inventory template
```

## Expected Benefits

1. **Scalability**: Automatic scaling based on actual demand
2. **Reliability**: Fault tolerance through multiple worker nodes
3. **Performance**: Dedicated database server and distributed load
4. **Cost Efficiency**: Scale down during low usage periods
5. **Maintainability**: Rolling updates without downtime

## Risk Mitigation

1. **Single Point of Failure**: Controller node backup and monitoring
2. **Network Latency**: Private network optimization
3. **Database Bottlenecks**: Connection pooling and optimization
4. **Scaling Delays**: Pre-emptive scaling based on trends
5. **Session Loss**: Database-backed session persistence

## Success Metrics

- Response time improvement: <500ms average
- Uptime target: 99.9%
- Auto-scaling response time: <5 minutes
- Cost optimization: 20-30% reduction during low usage
- Zero-downtime deployments achieved