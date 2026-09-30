# SIH26170 Backend

FastAPI Backend with ML inference and PostgreSQL integration.

## Database Setup

1. **Prerequisites**: PostgreSQL must be installed and running.
2. **Create Database**: Create a database named `sih26170` (or as configured) in your PostgreSQL server.
3. **Configuration**: Copy `.env.example` to `.env` and update the `DATABASE_URL`.
   ```bash
   cp .env.example .env
   ```
   *Format: `DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>`*
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run Migrations**: Apply the database schema using Alembic.
   ```bash
   alembic upgrade head
   ```
6. **Seed Data (Optional)**: Generate synthetic demo data.
   ```bash
   python -m app.db.seed
   ```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```

- **Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health) (reports API, models, and DB connection status)
