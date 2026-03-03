# Accounting System

A modular, full-featured accounting system built with Next.js and FastAPI, designed for team development.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (Neon)
- **File Storage**: Cloudinary
- **Authentication**: NextAuth.js + JWT

## Features

### Core Modules
- **Chart of Accounts**: Hierarchical account structure with 5 categories
- **General Ledger**: Double-entry accounting with audit trail
- **Journal Entries**: Manual entries with multi-currency support

### Accounts Receivable
- Customer management
- Sales invoices with line items
- Payment receipts
- Customer aging reports

### Accounts Payable
- Vendor/Supplier management
- Purchase bills
- Vendor payments
- AP aging reports

### Inventory Management
- Product catalog (Inventory, Non-Inventory, Service types)
- Multiple warehouses
- Purchase orders
- Stock movements and transfers
- Inventory valuation (FIFO, Weighted Average)

### Financial Reports
- Trial Balance
- Balance Sheet
- Income Statement (P&L)
- AR/AP Aging Reports
- Dashboard with KPIs

### Security
- Admin invite-only user registration
- Role-based access control (Admin, Accountant, Manager, Viewer)
- Comprehensive audit trail

## Project Structure

```
accounting-system/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities and API client
│   │   └── hooks/            # Custom React hooks
│   └── ...
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/v1/           # API routes
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   └── alembic/              # Database migrations
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Neon account)
- Cloudinary account (optional, for file uploads)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file from example:
   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your database URL and secrets:
   ```env
   DATABASE_URL=postgresql://username:password@host/database
   SECRET_KEY=your-secret-key-min-32-chars
   FRONTEND_URL=http://localhost:3000
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at http://localhost:8000
   API docs at http://localhost:8000/api/docs

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create `.env.local` file:
   ```bash
   cp .env.example .env.local
   ```

4. Update `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-nextauth-secret
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

   Frontend will be available at http://localhost:3000

### Default Login
- **Email**: admin@company.com
- **Password**: admin123

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env.example`

### Frontend (Vercel)

1. Import your repository to Vercel
2. Set the root directory to `frontend`
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL
   - `NEXTAUTH_SECRET`: Generate a secure secret
   - `NEXTAUTH_URL`: Your Vercel app URL

### Database (Neon)

1. Create a new project on Neon
2. Copy the connection string
3. Add it as `DATABASE_URL` in your backend environment

## Team Assignment

| Developer | Module | Responsibilities |
|-----------|--------|------------------|
| Lead | Core, Auth | Architecture, user management, security |
| Dev 1 | Chart of Accounts | Account types, hierarchy, GL |
| Dev 2 | Journal Entries | Transactions, multi-currency |
| Dev 3 | AR Module | Customers, invoices, payments |
| Dev 4 | AP Module | Vendors, bills, payments |
| Dev 5 | Inventory | Products, stock, POs |
| Dev 6 | Reports | Financial statements, dashboard |

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## License

MIT
