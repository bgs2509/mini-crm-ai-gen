# Deployment Guide

## Database Migrations

### Automatic Migrations

Database migrations are applied automatically when the application container starts. This is handled by the `entrypoint.sh` script which:

1. Waits for PostgreSQL to be ready
2. Runs `alembic upgrade head` to apply all pending migrations
3. Starts the application

**Important:** Migrations are idempotent - they can be run multiple times safely. If all migrations are already applied, the command will simply exit successfully without making any changes.

### How It Works

The `entrypoint.sh` script is configured in the Dockerfile:

```dockerfile
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This means:
- `ENTRYPOINT` runs first and executes the migration logic
- `CMD` is passed as arguments to the entrypoint (via `exec "$@"`)
- The application only starts after migrations complete successfully

### Data Persistence

Database data is stored in a Docker volume (`postgres_data`), which means:

- Data persists across container restarts
- Migrations don't delete or overwrite existing data
- When you restart containers with `docker compose restart` or `docker compose up`, your data remains intact

### Manual Migration Management

If you need to manage migrations manually:

```bash
# Check current migration version
docker compose exec app alembic current

# View migration history
docker compose exec app alembic history

# Create a new migration
docker compose exec app alembic revision -m "description"

# Upgrade to a specific version
docker compose exec app alembic upgrade <revision>

# Downgrade to a previous version
docker compose exec app alembic downgrade <revision>
```

### Production Considerations

For production deployments:

1. **Backup Before Migrations**: Always backup your database before applying migrations
   ```bash
   docker compose exec db pg_dump -U crm_user crm_db > backup.sql
   ```

2. **Test Migrations**: Test migrations in a staging environment first

3. **Zero-Downtime Deployments**: For zero-downtime deployments, consider:
   - Making migrations backward-compatible
   - Deploying code changes separately from schema changes
   - Using Blue-Green deployment strategy

4. **Monitoring**: Monitor the application logs during startup:
   ```bash
   docker compose logs -f app
   ```

### Troubleshooting

If migrations fail:

1. Check application logs:
   ```bash
   docker compose logs app
   ```

2. Check database connectivity:
   ```bash
   docker compose exec app pg_isready -h db -U crm_user -d crm_db
   ```

3. Manually check migration status:
   ```bash
   docker compose exec app alembic current
   docker compose exec app alembic history
   ```

4. If needed, you can skip the entrypoint and start a shell:
   ```bash
   docker compose run --entrypoint /bin/bash app
   ```
