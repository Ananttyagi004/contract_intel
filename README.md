# Contract Intelligence API

A production-ready Django-based API for intelligent contract analysis, field extraction, and risk assessment using AI-powered document processing.

## 🚀 Features

- **Document Ingestion**: Upload and process PDF contracts with automatic text extraction
- **Field Extraction**: AI-powered extraction of structured contract fields (parties, dates, terms, etc.)
- **Question Answering**: RAG-based Q&A over contract content with citations
- **Streaming Responses**: Real-time streaming answers using Server-Sent Events
- **Risk Assessment**: Automated detection of risky contract clauses and compliance issues
- **Background Processing**: Celery-based async processing with progress tracking
- **Comprehensive Admin**: Django admin interface for monitoring and management
- **OpenAPI Documentation**: Auto-generated API documentation with Swagger UI
- **Vector Search**: FAISS-based text chunking and embedding for intelligent document analysis

## 🏗️ Architecture

- **Backend**: Django 5.2 + Django REST Framework for REST APIs
- **Database**: PostgreSQL with normalized models for documents, pages, embeddings, and audit findings
- **Task Queue**: Celery + Redis for background processing (text extraction, field extraction, async tasks)
- **AI/ML**: Google Gemini models for embeddings and contract analysis
- **Vector Search**: FAISS for retrieval-augmented generation (RAG) and text chunking
- **Document Processing**: PyPDF2 for PDF ingestion, page splitting, and text extraction
- **Monitoring**: Health endpoints and comprehensive logging
- **Containerization**: Docker + Docker Compose for reproducible deployment and scaling

## 📋 API Endpoints

### Core Endpoints

- **Document Upload**: `POST /api/ingest/` - Upload and process PDF contracts
- **Field Extraction**: `POST /api/extract/` - Extract structured contract fields using AI
- **Document Q&A**: `POST /api/ask/` - Ask questions about contracts using RAG
- **Streaming Q&A**: `GET /api/ask/stream/` - Stream answers with Server-Sent Events
- **Contract Audit**: `POST /api/audit/` - Run automated risk assessment
- **Health Check**: `GET /healthz/` - System health status
- **Metrics**: `GET /metrics/` - System performance metrics

### API Documentation

- **Swagger UI**: `/api/docs/` - Interactive API documentation
- **ReDoc**: `/api/redoc/` - Alternative API documentation
- **OpenAPI Schema**: `/api/schema/` - Raw OpenAPI specification

## 🛠️ Setup & Installation

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key (for AI features)
- Python 3.8+ (for local development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd contract_intel
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your Google Gemini API key and other settings
   ```

3. **Start the services**
   ```bash
   make up
   # or manually: docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   make migrate
   # or manually: docker-compose exec web python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   make superuser
   # or manually: docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Docs: http://localhost:8000/api/docs/

### Alternative: Local Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   export DEBUG=1
   export SECRET_KEY=your-secret-key-here
   export OPENAI_API_KEY=your-gemini-api-key-here
   ```

3. **Run the application**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### Environment Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (for local development)
DATABASE_URL=postgres://postgres:postgres@localhost:5432/contract_intel

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your-gemini-api-key-here

# File Storage
MEDIA_URL=/media/
MEDIA_ROOT=media/

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 📖 Usage Examples

### 1. Upload a Contract

```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -H "Content-Type: multipart/form-data" \
  -F "files=@contract.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "Files uploaded successfully. Text extraction in progress.",
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "documents": [...]
}
```

### 2. Extract Contract Fields

```bash
curl -X POST http://localhost:8000/api/extract/ \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Contract fields extracted successfully using Gemini Flash LLM",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_method": "pure_llm_gemini_flash",
  "extracted_fields": {
    "parties": [...],
    "effective_date": "2024-01-15",
    "payment_terms": "Net 30 days",
    "auto_renewal": true,
    "governing_law": "California",
    "confidentiality": "Standard NDA terms apply"
  }
}
```

### 3. Ask Questions About Contracts (RAG)

```bash
curl -X POST http://localhost:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "query": "What are the payment terms in this contract?"
  }'
```

**Response:**
```json
{
  "answer": "The contract specifies payment terms of Net 30 days...",
  "citations": [
    {
      "page": 5,
      "start": 120,
      "end": 180
    }
  ]
}
```

### 4. Stream Answers (Server-Sent Events)

```bash
curl "http://localhost:8000/api/ask/stream/?document_id=550e8400-e29b-41d4-a716-446655440000&query=What%20are%20the%20payment%20terms?"
```

**Response (SSE stream):**
```
data: {"type": "token", "text": "The"}
data: {"type": "token", "text": " contract"}
data: {"type": "token", "text": " specifies..."}
data: {"type": "citations", "data": [{"page": 5, "start": 120, "end": 180}]}
data: {"type": "end"}
```

### 5. Run Contract Audit

```bash
curl -X POST http://localhost:8000/api/audit/ \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "findings": [
    {
      "finding_type": "auto_renewal",
      "severity": "high",
      "title": "Insufficient Auto-renewal Notice Period",
      "description": "Contract has auto-renewal with only 15 days notice",
      "risk_explanation": "Insufficient notice period may lead to unexpected renewals",
      "recommendation": "Ensure auto-renewal notice period is at least 30 days"
    }
  ]
}
```

## 🔧 Configuration

### Makefile Commands

The project includes a comprehensive Makefile for common operations:

```bash
make help          # Show all available commands
make up            # Start all services
make down          # Stop all services
make logs          # View logs from all services
make shell         # Open Django shell
make migrate       # Run database migrations
make test          # Run tests
make clean         # Clean up containers and images
make setup         # Complete initial setup
```

### Custom Field Extraction

Modify the extraction prompts in `ContractExtractionService` to extract additional contract fields.

### Risk Assessment Rules

Customize the audit analysis logic to add custom risk detection rules.

## 📊 Monitoring & Admin

### Django Admin

Access the admin interface at `/admin/` to:
- Monitor document processing status
- View extracted fields and audit findings
- Manage system configurations
- Track background tasks

### Health Checks

```bash
# System health
curl http://localhost:8000/healthz/

# Service status
make status
```

### Logs

View application logs:
```bash
make logs          # All services
make logs-web      # Web service only
make logs-celery   # Celery worker only
make logs-db       # Database only
```

## 🚀 Production Deployment

### Environment Variables

Set production values:
```bash
DEBUG=False
SECRET_KEY=<strong-secret-key>
ALLOWED_HOSTS=<your-domain>
OPENAI_API_KEY=<your-gemini-key>
```

### Database

Use production PostgreSQL:
```bash
DATABASE_URL=postgres://user:password@host:port/dbname
```

### Static Files

Collect and serve static files:
```bash
make collectstatic
```

### SSL/HTTPS

Configure reverse proxy (nginx) with SSL certificates.

## 🧪 Testing

### Run Tests
```bash
make test
make test-verbose  # With detailed output
```

### API Testing
Use the included Swagger UI at `/api/docs/` or tools like Postman.

## 📚 Supported Contract Types

The system works with any PDF contracts, including:
- NDAs (Non-Disclosure Agreements)
- MSAs (Master Service Agreements)
- Terms of Service documents
- Employment contracts
- Vendor agreements
- Service level agreements (SLAs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the Django admin interface for system status

## 🔮 Future Enhancements

- [ ] Multi-language contract support
- [ ] Advanced OCR for scanned documents
- [ ] Contract comparison and versioning
- [ ] Integration with e-signature platforms
- [ ] Advanced risk scoring algorithms
- [ ] Contract template generation
- [ ] Compliance checking against regulations
- [ ] Machine learning model fine-tuning
- [ ] Real-time collaboration features
- [ ] Advanced analytics and reporting 