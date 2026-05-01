# Text-to-SQL TUI App

A local, Dockerized natural-language-to-SQL application.

The user asks a question in a terminal UI, the backend asks a locally hosted model to generate SQL, executes the SQL against a PostgreSQL database seeded from `data.csv`, and returns the generated SQL plus the query result through SSE streaming to allow for a dynamic experience on the terminal.

## Project structure

I decided to create a monorepo with both `client` and `server` to separate concerns. Each module has its own Dockerfile and we have a `docker-compose` on root to have all the applications running.

```txt
.
├── apps
│   ├── client
│   │   ├── main.py              # TUI entrypoint
│   │   ├── api.py               # HTTP client
│   │   ├── config.py            # client env config
│   │   └── tui
│   │       ├── app.py           # Textual app/layout/events
│   │       ├── rendering.py     # Rich response rendering
│   │       └── widgets.py       # TUI widgets
│   └── server
│       ├── main.py              # FastAPI app factory
│       ├── config.py            # server env config
│       ├── database.py          # database connection/query execution
│       ├── models.py            # Pydantic models
│       ├── schema.py            # schema prompt context
│       ├── api
│       │   ├── routes.py        # API routes
│       │   └── sse.py           # SSE formatting
│       └── services
│           ├── ollama.py            # shared Ollama model client
│           ├── text_to_sql.py       # SQLCoder prompting/inference
│           ├── result_explainer.py  # SLM result-to-natural-language explanation
│           └── sql_guard.py         # SQL extraction/validation
├── db
│   └── init.sql                 # database schema + CSV import
├── data.csv                     # source dataset
├── docker-compose.yaml
└── README.md
```

## Requirements

- Docker
- Docker Compose

## How to run the project

### 1. Build and start all services detached

```bash
docker compose up --build -d
```

### 2. Pull the local models

The Ollama container needs the configured models available locally. Pull them once:

```bash
docker compose exec model ollama pull pxlksr/defog_sqlcoder-7b-2:Q2_KS && docker compose exec model ollama pull qwen2.5-coder:1.5b
```

### 3. Run the TUI

```bash
docker compose run --rm client
```

## Database

The database is initialized by `db/init.sql` when the Postgres container starts for the first time.

It creates a single `sales` table and imports `data.csv`:

## Design decisions and trade-offs

### Model choice

The default model is:

```txt
pxlksr/defog_sqlcoder-7b-2:Q2_KS
```

This model is specialized for text-to-SQL generation, which should improve SQL accuracy compared with a general coding model. The trade-off is that it is larger and may require more local resources.

A second lightweight SLM is used only after SQL execution to turn result rows into a short natural-language explanation. SQL generation still uses SQLCoder, and the UI keeps the generated SQL visible alongside the rows and explanation.

The explanation model defaults to:

```txt
qwen2.5-coder:1.5b
```

## Scaling the project

If the dataset grew to many larger tables, I would first make schema handling more explicit instead of injecting one static schema string. The backend could retrieve only the relevant schema fragments for each question before prompting the agent. I would also add indexes for common filters. We can also implement database replication in case of a huge ingress, and make tables into VIEWS for affordable SELECTs.

For high traffic, the services should be scaled independently:

- Run multiple API containers behind a load balancer.
- Keep Postgres as a managed/primary database with connection pooling, like PgBouncer.
- Deploy the models on a dedicated GPU-based VM, or use something like OpenRouter for inference.
- Add caching.

## AI usage

For this exercise I used [Pi](https://pi.dev/) as the coding-agent harness with GPT-5.5.

The assignment PDF text was provided as context, with the additional decision that the client should be a TUI rather than a web UI. The agent was also instructed to respect the single responsability principle to avoid dumping all logic into `main.py` when requesting changes.

### Skills

To improve the agent capabilities, i used the following skills:

- [/grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) Similar to a PLAN mode, used to talk about product definitions and understandment of the assignment with the agent.
- [minimalist-ui](https://www.ui-skills.com/skills/leonxlnx/minimalist-skill/) Im a fan of monochrome palletes and i wanted to have a minimalistic feeling for this agentic TUI
- [improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) Not heavily used, but its really nice to make the finishing touches on the overall arquitecture/structure of the repo.