# ClearLedger MVP

**Manual-first transaction logging for Zimbabwean merchants**

## Purpose

ClearLedger answers one question per day:

> "How much money did I actually receive today, and where is it stuck?"

This is a **behavior-testing instrument**, not a demo. It validates whether merchants will manually log transactions to track payment channels (EcoCash, ZIPIT, Bank, Paynow, Cash).

## Core Features

- **Manual Transaction Logging**: Create transactions with amount, channel, direction, status, and optional screenshot
- **Daily Truth Dashboard**: View totals by status (Expected, Received, Pending, Missing) grouped by channel
- **24h Flagging**: Visual alerts for Expected transactions older than 24 hours
- **Email Authentication**: Simple email/password login (one user = one business)

## Technology Stack

- **Frontend**: React + Vite + JavaScript + Tailwind CSS
- **Backend**: Python + FastAPI + SQLModel
- **Database**: PostgreSQL
- **Auth**: JWT tokens with passlib (bcrypt)

## Success Criteria

✅ A merchant can log a transaction in under 30 seconds  
✅ The daily truth screen needs zero explanation  
✅ The app survives 7 days of real use without breaking

## Kill Criteria

❌ **If users refuse to manually log transactions, the product is invalid and must be killed.**

This outcome is success. The MVP exists to validate behavior, not to scale.

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
createdb clearledger_db

# Create database user (optional, if not using default)
psql -c "CREATE USER clearledger WITH PASSWORD 'clearledger';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE clearledger_db TO clearledger;"

# Start backend (database tables will be created automatically)
uvicorn backend.app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

## Project Structure

```
cleartruthledger_mvp/
├── backend/           # FastAPI backend
│   └── app/
│       ├── api/       # API routes
│       ├── core/      # Security, config
│       ├── crud/      # Database operations
│       ├── db/        # Database setup
│       ├── models/    # SQLModel models
│       └── schemas/   # Pydantic schemas
├── client/            # React frontend
│   └── src/
│       ├── components/
│       ├── contexts/
│       ├── pages/
│       └── utils/
├── .env.example       # Environment template
├── requirements.txt   # Python dependencies
└── package.json       # Node dependencies
```

## Development Workflow

This project follows **strict commit discipline**:

- Every logical change = one commit
- Commits must be precise and factual
- Format: `[type]: description`
- Types: `chore`, `feat`, `fix`, `refactor`, `docs`, `test`

## License

MIT
