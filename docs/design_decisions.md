# Design Decisions & Trade-offs

## 1. Microservices vs Monolith
**Decision**: Modular Monolith / Service-Oriented Architecture.
**Rationale**: While a full microservices architecture offers scalability, it adds complexity. We chose a hybrid approach where the **Model Service** is decoupled from the **Backend API** via Docker. This allows us to scale inference independently (e.g., on GPU nodes) while keeping the business logic and database interactions tightly coupled for simplicity.

## 2. Model Selection: Specialized BERT vs Giant LLM
**Decision**: Fine-tuned BERT for classification + Small LLM (T5) for generation.
**Rationale**: 
- **Latency**: Detecting urgency must be near-instant. A 110M parameter BERT model runs in <50ms, whereas a large LLM (like GPT-4) call can take seconds.
- **Cost**: Hosting giant LLMs is expensive. T5-small/base can run on standard CPUs or consumer GPUs.
- **Privacy**: Local models ensure email data doesn't leave our infrastructure.

## 3. Storage: PostgreSQL + Redis
**Decision**: Relational DB for data, Redis for caching/queues.
**Rationale**:
- Email data is highly structured (sender, timestamp, body), making SQL a natural fit.
- Redis handles the high-throughput requirement for the "Draft Queue" and "Rate Limiting" better than a disk-based DB.

## 4. Framework: FastAPI vs Flask/Django
**Decision**: FastAPI.
**Rationale**: 
- Native async support is crucial for handling concurrent ML model requests and I/O bound database calls.
- Automatic standard documentation (Swagger UI) speeds up development and integration with the frontend.

## 5. Deployment: Docker Compose
**Decision**: Docker Compose for orchestration.
**Rationale**: Kubernetes is overkill for a single-node deployment. Docker Compose provides sufficient isolation and networking for our service mesh (API, DB, Redis, Model Server).

## Trade-offs
- **Complexity**: Managing two separate Python environments (one for API, one for ML) increases build times but prevents dependency conflicts (e.g., PyTorch vs Web libs).
- **Generation Quality**: T5-small is less creative than GPT-4 but is sufficient for professional, template-like email responses. We mitigate this with a **RAG** layer to inject context.
