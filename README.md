# Agente IA — Multi-tenant Conversational Agent for WhatsApp

Config-driven LangGraph engine. Each client gets its own prompt, tools, and model params — all resolved from DB at runtime. No code changes to onboard a new client.

## Architecture

```
Meta WhatsApp Cloud API
  ↓ webhook (POST /webhook)
FastAPI → Router (phone_number_id → client_id) → Queue → Worker LangGraph → DB → WhatsApp API
         ↕ 200 OK inmediato              (async)   ↑ config-driven
```

- **Webhook** — valida firma HMAC de Meta, responde 200 rápido, encola mensaje
- **Queue** — interfaz abstracta (Redis por defecto); el worker procesa asíncrono
- **Agent** — un solo grafo LangGraph; prompt, tools y modelo se resuelven por `client_id`
- **Tool Registry** — tools registradas una vez, habilitadas por cliente en DB
- **Observability** — cada turno, tool call y error se loguea asíncrono para dashboard futuro
- **Multi-tenant isolation** — toda query DB filtra por `client_id` (por diseño, no por convención)

## Quickstart

```bash
# Requisitos: Python 3.13+, PostgreSQL, Redis
pip install -e ".[dev]"

# Iniciar DB + cola
docker compose up -d

# Copiar y completar .env
cp .env.example .env

# Correr migraciones
python scripts/migrate.py

# Seed un cliente de prueba
python scripts/seed_client.py --client-id demo --phone 123456789 --prompt "Eres un asistente útil."

# Iniciar servidor
uvicorn src.main:app --reload --port 8000
```

## Commands

| Comando | Acción |
|---------|--------|
| `python -m pytest tests/ -v` | Tests unitarios + integración |
| `ruff check .` | Lint |
| `ruff format .` | Formatear código |
| `python scripts/migrate.py` | Ejecutar migraciones SQL |
| `python scripts/seed_client.py --help` | Seed de cliente de prueba |

## Project Structure

```
src/
├── webhook/          # POST /webhook, validación firma, resolver client_id
├── queue/            # Interface abstracta de cola + worker
├── agent/            # Grafo LangGraph (único, config-driven)
│   └── nodes/        # interpret, tool_executor, responder
├── tools/            # Registry central + BaseTool
│   └── builtin/      # Tools concretas (get_weather, etc.)
├── config/           # ClientConfig, loader con cache
├── persistence/      # Repository con filtro obligatorio de client_id
│   └── migrations/   # SQL migraciones versionadas
├── observability/    # EventLogger asíncrono (cola + batch flush)
├── whatsapp/         # Cliente outbound para Meta API
└── main.py           # FastAPI app
```

## Pending Architecture Decisions

- Mecanismo de cola concreto (hoy: interfaz abstracta)
- Pool de conexiones SQLAlchemy async
- Integración LLM concreta (OpenRouter vs OpenAI)
- Dashboard de conversaciones
- Despliegue (Render / Railway / VPS)
