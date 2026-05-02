# Text-to-SQL TUI App

A local, Dockerized natural-language-to-SQL application.

The user asks a question in a terminal UI, the backend asks a locally hosted model to generate SQL, executes the SQL against a PostgreSQL database seeded from `data.csv`, and returns the generated SQL plus the query result through SSE streaming to allow for a dynamic experience on the terminal.

## 🚨 Important: local model requirements

To comply with the assignment requirements, this project hosts local Ollama models instead of calling an external API.

Models used:

- SQL generation: `pxlksr/defog_sqlcoder-7b-2:Q2_KS`
- Result explanation: `qwen2.5-coder:1.5b`

Recommended Docker memory allocation:

- Minimum: 6 GB
- Recommended: 8 GB+

Theres a specific section about trade-offs later in the document with deeper details, but im choosing to host a heavier model (SQLCoder-7b) in favor of precision and accuracy. Even though im a big fan of trying to have optimizations for lower-end servers, 6gb of ram does not seem like a big ask to test the demo.

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

### 1. Build and start the backend services

```bash
docker compose up --build -d
```

On the first run, the `model-init` one-shot container downloads the local Ollama models into the shared `ollama` Docker volume. This can take several minutes depending on your connection and machine. Later runs reuse the cached models.

### 2. Run the TUI

```bash
docker compose run --rm client
```

The TUI client is behind a Compose profile, so it does not start in the background during `docker compose up`.

## Database

The database is initialized by `db/init.sql` when the Postgres container starts for the first time.

It creates a single `sales` table and imports `data.csv`.

## Model initialization

The Ollama service is long-running, while `model-init` is a temporary setup container. `model-init` waits for Ollama to become healthy, pulls the configured models, stores them in the shared `ollama` volume, and exits successfully. The API server only starts after the database is healthy and `model-init` has completed.

Default models:

- SQL generation: `pxlksr/defog_sqlcoder-7b-2:Q2_KS`
- Result explanation: `qwen2.5-coder:1.5b`

## Design decisions and trade-offs

### Model choice

The default model is:

```txt
pxlksr/defog_sqlcoder-7b-2:Q2_KS
```

This model is specialized for text-to-SQL generation, which improves SQL accuracy compared with a general coding model. The trade-off is that it is larger and may require more local resources, but for the current scenario i believe its worth it.

A second lightweight SLM is used only after SQL execution to turn result rows into a short natural-language explanation. SQL generation still uses SQLCoder, and the UI keeps the generated SQL visible alongside the rows and explanation.

The explanation model defaults to:

```txt
qwen2.5-coder:1.5b
```

### Monorepo

I firmly believe that monorepos can be a double-edged sword for fast-moving teams. On one hand, they make it easy to iterate quickly and keep everything in one place, which improves visibility and collaboration. On the other, they can become difficult to scale if boundaries are not well defined, especially when evolving toward microservices or a larger more complex architecture.

A well-structured monorepo can provide strong separation of concerns through defined modules, while still benefiting from shared tooling, consistent standards, and simpler dependency management.

Even with modular separation, it’s important to be intentional about how components interact. Particular attention should be paid to:

- how database access is owned and exposed across modules
- how shared packages and libraries are designed and constrained
- how public interfaces are defined and enforced

Without these guardrails, a monorepo can easily drift into tight coupling, making future scaling and service extraction significantly harder.

In the case of this project, a monorepo fits well as we do not have many moving parts, so even though this repo may not follow 100% best practices of monorepos, we can still make it work fairly easy in case of a migration.

### TUI

The terminal has become a nice place for agents and developers to work on, but this project will appeal more to power-users rather than individuals that prefer to work with web-based UI's or similar.

## Scaling the project

### Bigger dataset

- **Make schema handling more explicit**: We can use VIEWS like `information_schema` of PostgreSQL to get information about the tables, and only fetch the necessary entities for the model.
- **Indexing**: Indexes for common filters/columns on the database like date, quantity, etc.
- **Database replication**: Create read-replicas of a main Database to read from.
- **Materialized VIEWS**: For data that is not needed in-real time, we can use MATERIALIZED VIEWS to reduce read costs.

### High traffic

For high traffic, the services should be scaled independently:

- **Load balancing**: Run multiple API containers and redirect traffic with load balancing.
- **Connection pooling**: Keep Postgres as a managed/primary database with connection pooling, like PgBouncer.
- **Dedicated GPU-based VMs**: Deploy the models on a dedicated GPU-based VM, or use an external provider like OpenRouter for inference.
- **Caching**: Add caching with redis for frequent LLM responses.

This project uses a TUI, so there are no browser static assets to scale or cache. If this became a web application, the frontend could be built as static assets and served through a CDN such as Cloudflare. That would make the UI cheap and globally cacheable.

## AI usage

For this exercise I used [Pi](https://pi.dev/) as the coding-agent harness with GPT-5.5.

The assignment PDF text was provided as context, with the additional decision that the client should be a TUI rather than a web UI. The agent was also instructed to respect the single responsability principle to avoid dumping all logic into `main.py` when requesting changes.

### Skills

To improve the agent capabilities, i used the following skills:

- [/grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) Similar to a PLAN mode, used to talk about product definitions and understandment of the assignment with the agent.
- [minimalist-ui](https://www.ui-skills.com/skills/leonxlnx/minimalist-skill/) I wanted to use monochrome palletes for a minimalistic feeling on this agentic TUI.
- [improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) Not heavily used, but its really nice to make the finishing touches on the overall architecture/structure of the repo to see if im missing something.
