# AI Answer Sheet Evaluation System - Backend

A comprehensive backend system for automatically evaluating handwritten answer sheets using AI technologies including OpenAI Vision API, Gemini AI, and advanced NLP techniques.

## Features

- **OCR Processing**: Extract handwritten text from answer sheet images using OpenAI Vision API
- **Intelligent Evaluation**: Concept-based evaluation using semantic similarity and keyword matching
- **Verification Layer**: Double-check evaluations using Gemini AI for quality assurance
- **Manual Review System**: Queue system for scripts requiring human review
- **Async Processing**: Handle large batches efficiently with Celery and Redis
- **Real-time Updates**: WebSocket support for live progress tracking
- **Email Notifications**: Automated notifications for batch completion and reviews
- **Secure Authentication**: JWT-based authentication with role-based access control

## Architecture

### Tech Stack
- **Framework**: FastAPI with Python 3.8+
- **Database**: MongoDB with Motor (async driver)
- **AI Services**: OpenAI Vision API, Google Gemini AI
- **ML Libraries**: Sentence Transformers, OpenCV, Pillow
- **Task Queue**: Celery with Redis backend
- **Authentication**: JWT with bcrypt password hashing

### Core Components
1. **OCR Service**: Handwritten text extraction and question segmentation
2. **Evaluation Service**: Concept-based scoring with confidence metrics
3. **Verification Service**: AI-powered evaluation verification
4. **Notification Service**: Email notifications for system events
5. **File Management**: Secure image upload and storage
6. **Manual Review**: Queue system for human oversight

## Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Redis 6.0+
- OpenAI API Key
- Google Gemini AI API Key

### Setup

1. **Clone and Navigate**
   ```bash
   cd ai-evaluation-backend
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Copy `.env` file and update with your credentials:
   ```env
   # Database
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=ai_evaluation_system

   # AI APIs
   OPENAI_API_KEY=your-openai-api-key
   GEMINI_API_KEY=your-gemini-api-key

   # Redis for async processing
   REDIS_URL=redis://localhost:6379

   # Email notifications
   EMAIL_USER=your-email@example.com
   EMAIL_PASSWORD=your-email-password
   ```

5. **Start Services**
   
   **Terminal 1 - Main API Server**
   ```bash
   python -m app.main
   ```
   
   **Terminal 2 - Celery Worker**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info --queues=evaluation,batch
   ```
   
   **Terminal 3 - Celery Beat (Optional - for scheduled tasks)**
   ```bash
   celery -A app.workers.celery_app beat --loglevel=info
   ```

## API Documentation

### Base URL
- Development: `http://localhost:8000`
- API Prefix: `/api`

### Authentication Endpoints
- `POST /api/auth/register` - Register new professor
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh JWT token

### Evaluation Schemes
- `POST /api/schemes/` - Create evaluation scheme
- `GET /api/schemes/` - List user's schemes
- `GET /api/schemes/{id}` - Get specific scheme
- `PUT /api/schemes/{id}` - Update scheme
- `DELETE /api/schemes/{id}` - Delete scheme
- `POST /api/schemes/{id}/upload-file` - Upload scheme PDF

### Exam Sessions
- `POST /api/sessions/` - Create exam session
- `GET /api/sessions/` - List sessions
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/progress` - Get processing progress

### Answer Scripts
- `POST /api/scripts/upload-batch` - Upload multiple scripts
- `POST /api/scripts/upload-single` - Upload single script
- `GET /api/scripts/{session_id}/status` - Get session scripts status
- `GET /api/scripts/{script_id}/details` - Get script details

### Evaluations
- `POST /api/evaluations/process-script/{script_id}` - Process single script
- `GET /api/evaluations/{session_id}/results` - Get session results
- `GET /api/evaluations/{script_id}/detailed` - Get detailed evaluation
- `GET /api/evaluations/review-queue` - Get manual review queue
- `POST /api/evaluations/{review_id}/manual-review` - Submit manual review

### System
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation
- `GET /redoc` - ReDoc API documentation

## Usage Examples

### 1. Register and Login
```bash
# Register
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "professor@university.edu",
    "full_name": "Dr. John Smith",
    "university": "Tech University",
    "department": "Computer Science",
    "password": "secure_password"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=professor@university.edu&password=secure_password"
```

### 2. Create Evaluation Scheme
```bash
curl -X POST "http://localhost:8000/api/schemes/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheme_name": "Data Structures Mid-term",
    "subject": "Computer Science",
    "total_marks": 100,
    "passing_marks": 40,
    "questions": [
      {
        "question_number": 1,
        "max_marks": 20,
        "concepts": [
          {
            "concept": "Binary tree definition and properties",
            "keywords": ["binary tree", "node", "left", "right", "parent", "child"],
            "weight": 0.6,
            "marks_allocation": 12
          }
        ]
      }
    ]
  }'
```

### 3. Upload Answer Scripts
```bash
curl -X POST "http://localhost:8000/api/scripts/upload-batch" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "session_id=SESSION_ID" \
  -F "files=@answer1.jpg" \
  -F "files=@answer2.jpg"
```

## Processing Pipeline

### 1. OCR Stage
- Image preprocessing (rotation correction, noise reduction, contrast enhancement)
- Handwritten text extraction using OpenAI Vision API
- Question number detection and text segmentation
- Confidence scoring for OCR quality

### 2. Evaluation Stage
- Concept extraction from student answers
- Semantic similarity calculation using Sentence Transformers
- Keyword matching with weighted scoring
- Individual question evaluation with detailed breakdown

### 3. Verification Stage
- Gemini AI verification of evaluation accuracy
- Cross-validation of scores against marking scheme
- Confidence scoring and adjustment suggestions
- Flagging for manual review when necessary

### 4. Review Stage
- Automatic flagging based on confidence thresholds
- Priority-based queue management
- Manual override capabilities for professors
- Audit trail for all manual interventions

## Configuration

### Processing Modes
- **Real-time**: ≤5 scripts processed immediately
- **Async**: >5 scripts queued for batch processing

### Confidence Thresholds
- OCR Confidence: <0.6 flags for manual review
- Evaluation Confidence: <0.7 flags for manual review
- Verification Confidence: <0.8 flags for manual review

### File Handling
- Supported formats: JPG, PNG, BMP, TIFF
- Maximum file size: 10MB (configurable)
- Automatic image preprocessing and optimization

## Error Handling

### OCR Failures
- Automatic retry with different preprocessing
- Fallback to manual transcription queue
- Detailed error logging and reporting

### Evaluation Errors
- Graceful degradation with simplified scoring
- Manual review flagging for complex cases
- Error context preservation for debugging

### System Resilience
- Database connection retry logic
- API timeout handling with exponential backoff
- Task failure recovery and requeuing

## Monitoring and Logging

### Metrics Tracked
- Processing success/failure rates
- Average processing time per script
- OCR and evaluation confidence scores
- Manual review queue statistics

### Log Levels
- INFO: Normal operations and progress
- WARNING: Non-critical issues and fallbacks
- ERROR: Failures requiring attention
- DEBUG: Detailed processing information

## Security Features

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Role-based access control

### File Security
- Secure file upload with validation
- Virus scanning integration ready
- Temporary file cleanup
- Access logging and audit trails

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration for frontend integration
- HTTPS enforcement in production

## Performance Optimization

### Database
- Strategic indexing for query performance
- Connection pooling for concurrent requests
- Aggregation pipelines for complex queries

### Image Processing
- Asynchronous processing pipeline
- Memory-efficient image handling
- Parallel processing for batch operations

### Caching
- Redis caching for frequent queries
- File-based caching for processed images
- In-memory caching for evaluation schemes

## Deployment

### Development
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production
- Use Gunicorn with multiple workers
- Configure reverse proxy (Nginx)
- Set up SSL certificates
- Enable monitoring and logging
- Configure automated backups

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Verify MongoDB is running
   - Check connection string in .env
   - Ensure network connectivity

2. **Redis Connection Failed**
   - Start Redis server
   - Verify Redis URL configuration
   - Check firewall settings

3. **OpenAI API Errors**
   - Verify API key validity
   - Check quota and billing
   - Monitor rate limits

4. **File Upload Issues**
   - Check file size limits
   - Verify upload directory permissions
   - Ensure disk space availability

### Debug Mode
Set environment variable for detailed logging:
```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
python -m app.main
```

## Contributing

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Maintain comprehensive documentation
- Write unit tests for new features

### Development Workflow
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit pull request
5. Pass code review

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For technical support or questions:
- Create an issue on GitHub
- Email: support@ai-evaluation-system.com
- Documentation: [Project Wiki](https://github.com/project/wiki)

---

**Note**: This system requires proper API keys and infrastructure setup. Ensure all dependencies are correctly configured before deployment.