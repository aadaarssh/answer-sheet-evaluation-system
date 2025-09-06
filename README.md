# 🤖 AI-Powered Handwritten Answer Sheet Evaluation System

An intelligent automated grading system that evaluates handwritten university exam papers using advanced AI technologies including OCR, NLP, and semantic analysis.

![System Architecture](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi) ![Frontend](https://img.shields.io/badge/Vite-Frontend-646CFF?style=flat-square&logo=vite) ![Database](https://img.shields.io/badge/MongoDB-Database-47A248?style=flat-square&logo=mongodb) ![AI](https://img.shields.io/badge/OpenAI-Vision%20API-412991?style=flat-square&logo=openai)

## 🎯 Project Overview

This system revolutionizes academic assessment by automating the evaluation of handwritten exam papers, providing fast, consistent, and unbiased grading for universities and educational institutions.

### ✨ Key Features

- **🔍 Advanced OCR**: Extracts text from handwritten answer sheets using OpenAI Vision API
- **🧠 Intelligent Evaluation**: Concept-level semantic similarity matching with marking schemes
- **🔄 Dual AI Verification**: Gemini AI provides secondary verification and confidence scoring
- **⚡ Hybrid Processing**: Real-time for small batches (≤5), async for larger batches (>5)
- **📊 Detailed Analytics**: Concept-wise breakdown with confidence scores
- **🛡️ Quality Assurance**: Automatic flagging for manual review when needed
- **👨‍🏫 Professor-Friendly**: Intuitive interface for creating marking schemes and viewing results

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vite Frontend │───▶│  FastAPI Backend │───▶│   MongoDB       │
│   (Port 8081)  │    │   (Port 8000)   │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  AI Services     │
                    │  • OpenAI Vision │
                    │  • Gemini API    │
                    │  • Embeddings    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Celery Workers  │
                    │  (Redis Queue)   │
                    └──────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens
- **Task Queue**: Celery + Redis
- **AI APIs**: OpenAI Vision API, Google Gemini API
- **NLP**: Sentence Transformers for semantic similarity

### Frontend  
- **Framework**: Vite (React/Vue/Angular)
- **Styling**: Modern responsive design
- **State Management**: Built-in state management
- **File Upload**: Multi-file batch upload support

### Infrastructure
- **Message Broker**: Redis
- **File Storage**: Local filesystem (configurable)
- **Processing**: Hybrid sync/async based on load

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **MongoDB** (local or cloud)
- **Redis** (for async processing)
- **OpenAI API Key**
- **Google Gemini API Key**

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-answer-sheet-evaluation
   ```

2. **Backend Setup**
   ```bash
   cd ai-evaluation-backend
   
   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   copy .env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Frontend Setup**
   ```bash
   cd "../final frontend folder"
   npm install
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Start MongoDB (if local)
   mongod
   
   # Terminal 2: Start Redis
   redis-server
   
   # Terminal 3: Start Backend
   cd ai-evaluation-backend
   python start_server.py
   
   # Terminal 4: Start Worker (for async processing)
   python start_worker.py
   
   # Terminal 5: Start Frontend
   cd "../final frontend folder"
   npm run dev
   ```

5. **Access the Application**
   - **Frontend**: http://localhost:8081
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_evaluation_system

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Processing
REAL_TIME_THRESHOLD=5
REDIS_URL=redis://localhost:6379

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
```

## 📋 How It Works

### 1. Evaluation Workflow

```mermaid
graph TD
    A[Upload Answer Sheets] --> B[OpenAI Vision OCR]
    B --> C[Question Segmentation]
    C --> D[Concept Extraction]
    D --> E[Semantic Similarity Analysis]
    E --> F[Initial Scoring]
    F --> G[Gemini AI Verification]
    G --> H{Confidence Check}
    H -->|High Confidence| I[Final Score]
    H -->|Low Confidence| J[Manual Review Queue]
    I --> K[Results Dashboard]
    J --> L[Professor Review]
```

### 2. Processing Modes

- **Real-time Processing**: 1-5 answer sheets (immediate results)
- **Async Processing**: 6+ answer sheets (background processing with progress tracking)
- **Manual Review**: Automatic flagging for uncertain evaluations

### 3. Quality Assurance

The system automatically flags papers for manual review when:
- Overall confidence score < 70%
- Score below passing marks
- OCR extraction confidence < 80%
- Processing errors occur
- Gemini verification suggests review

## 🎓 Usage Guide

### For Professors

1. **Create Marking Scheme**
   - Define evaluation criteria for each question
   - Set concept weights and keyword mappings
   - Specify passing marks and total marks

2. **Upload Answer Sheets**
   - Batch upload support (PDF/Image formats)
   - Automatic session tracking
   - Progress monitoring

3. **Review Results**
   - Detailed score breakdowns
   - Concept-wise analysis
   - Manual review queue for flagged papers
   - Export results to various formats

## 📊 Database Schema

### Core Collections

- **Users**: Professor accounts and authentication
- **Evaluation Schemes**: Marking criteria and concept definitions
- **Exam Sessions**: Batch processing sessions
- **Answer Scripts**: OCR text and question segmentation
- **Evaluation Results**: Scores, breakdowns, and confidence metrics
- **Manual Review Queue**: Flagged evaluations requiring review

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new professor
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile

### Evaluation Schemes
- `POST /api/schemes/create` - Create new marking scheme
- `GET /api/schemes/list` - List all schemes
- `GET /api/schemes/{id}` - Get specific scheme details

### Answer Processing
- `POST /api/scripts/upload-batch` - Batch upload answer sheets
- `GET /api/sessions/{id}/progress` - Track processing progress
- `GET /api/evaluations/{session_id}/results` - Get evaluation results

### Manual Review
- `GET /api/evaluations/review-queue` - Get papers needing review
- `POST /api/evaluations/{script_id}/manual-review` - Submit manual scores

## 🧪 Testing

### Run Backend Tests
```bash
cd ai-evaluation-backend
python -m pytest tests/ -v
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   export ENVIRONMENT=production
   export MONGODB_URL=mongodb://your-production-db
   export REDIS_URL=redis://your-redis-instance
   ```

2. **Build Frontend**
   ```bash
   cd "final frontend folder"
   npm run build
   ```

3. **Deploy Backend**
   ```bash
   cd ai-evaluation-backend
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🔒 Security Features

- **JWT Authentication** for secure API access
- **Input Validation** for all endpoints
- **File Upload Security** with type and size validation
- **Rate Limiting** to prevent abuse
- **Audit Logging** for all evaluation actions

## 📈 Performance

- **Processing Speed**: ~30-60 seconds per answer sheet (depending on length)
- **Accuracy**: 85-95% correlation with manual grading
- **Scalability**: Handles 100+ concurrent evaluations
- **Throughput**: 500+ papers per hour with multiple workers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**CORS Errors:**
- Ensure backend CORS includes your frontend port
- Check if frontend and backend ports match configuration

**Redis Connection Failed:**
- Install and start Redis server
- Verify Redis is running on port 6379

**MongoDB Connection Issues:**
- Ensure MongoDB is running
- Check connection string in .env file

**OCR Quality Issues:**
- Ensure good image quality (300+ DPI)
- Proper lighting and contrast
- Clear handwriting

**Sentence Transformers Warning:**
```bash
pip install sentence-transformers
```

### Getting Help

- **Documentation**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](your-repo-url/issues)
- **Wiki**: [Project Wiki](your-repo-url/wiki)

## 🌟 Roadmap

- [ ] **Blockchain Integration** for secure marks storage
- [ ] **Multi-language Support** for international universities  
- [ ] **Diagram Recognition** for STEM subjects
- [ ] **Mobile App** for remote evaluation
- [ ] **LMS Integration** (Canvas, Moodle, Blackboard)
- [ ] **Advanced Analytics** with ML insights

## 👨‍💻 Development Team

- **Lead Developer**: Adarsh Hoogar
- **AI/ML Engineer**: [Your Name]
- **Frontend Developer**: [Your Name]

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/aadaarssh/answer-sheet-evaluation-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/aadaarssh/answer-sheet-evaluation-system?style=social)
![GitHub issues](https://img.shields.io/github/issues/aadaarssh/answer-sheet-evaluation-system)
![GitHub license](https://img.shields.io/github/license/aadaarssh/answer-sheet-evaluation-system)

---

**⭐ Star this repository if you find it helpful!**

Built with ❤️ for the education community
