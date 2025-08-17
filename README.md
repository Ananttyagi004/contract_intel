# Contract Intelligence API

A production-ready Django-based API for intelligent contract analysis, field extraction, question answering, and risk assessment.

## 🚀 Features

- **Document Ingestion**: Upload and process PDF contracts with automatic text extraction
- **Field Extraction**: AI-powered extraction of structured contract fields (parties, dates, terms, etc.)
- **Question Answering**: RAG-based Q&A over contract content with citations
- **Risk Assessment**: Automated detection of risky contract clauses
- **Background Processing**: Celery-based async processing with progress tracking
- **Webhook Support**: Real-time notifications for completed tasks
- **Comprehensive Admin**: Django admin interface for monitoring and management
- **OpenAPI Documentation**: Auto-generated API documentation with Swagger UI

## 🏗️ Architecture

- **Backend**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL with comprehensive models
- **Task Queue**: Celery + Redis for background processing
- **AI/ML**: OpenAI GPT-4 for field extraction and Q&A
- **Vector Search**: FAISS for RAG-based question answering
- **Document Processing**: PyPDF2 + textract for PDF text extraction
- **Containerization**: Docker + Docker Compose for easy deployment

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/` | Upload contract documents |
| `GET` | `/api/documents/` | List all documents |
| `GET` | `/api/documents/{id}/` | Get document details |
| `POST` | `/api/documents/{id}/extract_fields/` | Manually trigger field extraction |
| `POST` | `/api/documents/{id}/run_audit/` | Manually trigger audit analysis |
| `GET` | `/api/documents/{id}/status/` | Get processing status |

### Field Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/extracted-fields/` | List extracted fields |
| `GET` | `/api/extracted-fields/{id}/` | Get extracted fields for a document |
| `GET` | `/api/extracted-fields/summary/` | Get extraction statistics |

### Question Answering

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/questions/ask/` | Ask a question about contracts |
| `GET` | `/api/questions/` | List all questions |
| `GET` | `/api/questions/{id}/` | Get question details |
| `GET` | `/api/ask/stream/{id}/` | Stream question answer generation |

### Audit & Risk Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/audit-findings/` | List audit findings |
| `GET` | `/api/audit-findings/{id}/` | Get audit finding details |
| `GET` | `/api/audit-findings/summary/` | Get audit statistics |
| `GET` | `/api/audit-findings/high_risk/` | Get high-risk findings |

### Admin & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/healthz/` | Health check |
| `GET` | `/api/metrics/` | System metrics |
| `GET` | `/api/docs/` | Swagger UI documentation |
| `GET` | `/api/schema/` | OpenAPI schema |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/webhooks/configure/` | Configure webhook endpoints |
| `GET` | `/api/webhooks/` | List webhook events |

## 🛠️ Setup & Installation

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for AI features)
- PostgreSQL (included in Docker setup)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ContractIntelligence
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Docs: http://localhost:8000/api/docs/

### Environment Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/contract_intel

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

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
curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: multipart/form-data" \
  -F "title=Service Agreement" \
  -F "file=@contract.pdf"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Service Agreement",
  "status": "uploaded",
  "uploaded_at": "2024-01-15T10:30:00Z"
}
```

### 2. Ask a Question

```bash
curl -X POST http://localhost:8000/api/questions/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What are the payment terms in the contract?",
    "document_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

**Response:**
```json
{
  "message": "Question submitted for processing",
  "question_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending"
}
```

### 3. Get Question Answer

```bash
curl http://localhost:8000/api/questions/660e8400-e29b-41d4-a716-446655440001/
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "question_text": "What are the payment terms in the contract?",
  "answer": "The contract specifies payment terms of Net 30 days...",
  "citations": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "text": "Payment shall be made within 30 days...",
      "page_number": 5
    }
  ],
  "status": "completed"
}
```

### 4. Check Processing Status

```bash
curl http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/status/
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percentage": 75,
  "current_step": "Running audit analysis"
}
```

### 5. Get Audit Findings

```bash
curl http://localhost:8000/api/audit-findings/?document=550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "results": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
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

### Webhook Setup

Configure webhooks to receive notifications when tasks complete:

```bash
curl -X POST http://localhost:8000/api/webhooks/configure/ \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-app.com/webhooks",
    "event_types": ["document_processed", "question_answered", "audit_completed"]
  }'
```

### Custom Risk Rules

Modify `AuditAnalysisService` in `services.py` to add custom risk detection rules.

### Field Extraction

Customize the extraction prompt in `FieldExtractionService` to extract additional fields.

## 📊 Monitoring & Admin

### Django Admin

Access the admin interface at `/admin/` to:
- Monitor document processing status
- View extracted fields and audit findings
- Manage webhook configurations
- Track background tasks

### Health Checks

```bash
# System health
curl http://localhost:8000/healthz/

# System metrics
curl http://localhost:8000/api/metrics/
```

### Logs

View application logs:
```bash
docker-compose logs web
docker-compose logs celery
docker-compose logs redis
```

## 🚀 Production Deployment

### Environment Variables

Set production values:
```bash
DEBUG=False
SECRET_KEY=<strong-secret-key>
ALLOWED_HOSTS=<your-domain>
OPENAI_API_KEY=<your-openai-key>
```

### Database

Use production PostgreSQL:
```bash
DATABASE_URL=postgres://user:password@host:port/dbname
```

### Static Files

Collect and serve static files:
```bash
python manage.py collectstatic
```

### SSL/HTTPS

Configure reverse proxy (nginx) with SSL certificates.

## 🧪 Testing

### Run Tests
```bash
docker-compose exec web python manage.py test
```

### API Testing
Use the included Swagger UI at `/api/docs/` or tools like Postman.

## 📚 Sample Contracts

The system works with any PDF contracts. For testing, you can use:
- NDAs (Non-Disclosure Agreements)
- MSAs (Master Service Agreements)
- Terms of Service documents
- Employment contracts
- Vendor agreements

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