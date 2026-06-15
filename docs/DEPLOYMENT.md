# Production Deployment Guide

## Prerequisites

- Docker and Docker Compose
- TLS certificate (Let's Encrypt or institution CA)
- Secrets management for `SECRET_KEY`, `GEMINI_API_KEY`, database credentials

## HTTPS with Caddy (recommended)

Example `Caddyfile`:

```
your-domain.example.org {
    reverse_proxy frontend:5173
}

your-domain.example.org/api/* {
    reverse_proxy backend:8000
}
```

Ensure `CORS_ORIGINS` includes your production domain.

## Encryption at Rest

- **PostgreSQL:** Use encrypted volumes (LUKS, cloud provider encryption, or managed DB)
- **Exports:** The `exports_data` Docker volume stores generated artifacts; encrypt at the host/volume level

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing key (32+ random bytes) |
| `GEMINI_API_KEY` | Gemini API key |
| `LLM_MODEL` | LiteLLM model string |
| `LOCAL_MODEL_ENABLED` | `true` to use Ollama/local model |
| `OLLAMA_API_BASE` | Ollama endpoint when local enabled |
| `MAX_ACTIVE_DATASETS` | Limit enabled datasets (default: 1) |
| `SESSION_RETENTION_DAYS` | Days before sessions are eligible for cleanup |
| `INSTITUTION_NAME` | Appears in exported documents |

## Session Retention

Configure `SESSION_RETENTION_DAYS` (default: 90). A cleanup job can be scheduled:

```bash
# Example cron — extend with a management command as needed
docker compose exec backend python -c "print('Review sessions older than retention policy')"
```

## Compliance Checklist

- [ ] HTTPS enabled for all traffic
- [ ] Secrets not committed to version control
- [ ] Database backups configured
- [ ] Audit log reviewed periodically
- [ ] RBAC verified (researchers cannot access admin)
- [ ] Export watermarking verified on docx and scripts
- [ ] LLM provider BAA/data processing agreement in place (if applicable)

## Local / Private LLM

When `LOCAL_MODEL_ENABLED=true`, LiteLLM routes to Ollama:

```
LOCAL_MODEL_ENABLED=true
OLLAMA_API_BASE=http://your-ollama-host:11434
LLM_MODEL_LOCAL=ollama/llama3
```

Run Ollama on the same host or a private network accessible from the backend container.

## Backup

```bash
docker compose exec db pg_dump -U hra hra > backup.sql
```

Restore:

```bash
cat backup.sql | docker compose exec -T db psql -U hra hra
```
