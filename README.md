# TPA - The Personal Assistant

TPA is an AI-powered personal assistant application that helps users plan trips, search for flights and hotels, and get travel information through natural language conversations. Built with a modern tech stack featuring FastAPI backend and React frontend.

## Overview

TPA combines the power of large language models (GPT-4o-mini) with real-time search capabilities to provide intelligent travel planning assistance. Users can interact with the AI agent through a conversational interface, asking questions about flights, hotels, and travel news in natural language.

## Features

### Core Capabilities

- **Intelligent Chat Interface**: Natural language conversations with an AI agent powered by LangGraph and GPT-4o-mini
- **Flight Search**: Search for flights between cities with flexible date handling (understands relative dates like "tomorrow", "next week")
- **Hotel Search**: Find hotels at destinations with customizable check-in/check-out dates
- **Travel News**: Get latest travel news and destination information
- **Conversation History**: Persistent chat sessions that survive page refreshes
- **Session Management**: Multiple chat sessions with sidebar navigation

### User Interface

- **Modern Glassmorphism Design**: Clean, transparent UI with subtle gradients and smooth animations
- **Light/Dark Mode**: Toggle between light and dark themes
- **Responsive Layout**: Works seamlessly on desktop and mobile devices
- **Interactive Hotel Cards**: Click on hotel cards to view image galleries with all property photos
- **Booking Integration**: Direct links to hotel websites or Google Hotels search
- **Image Gallery**: Full-screen modal with carousel navigation for viewing hotel images
- **Structured Data Display**: Beautiful cards for hotels, flights, and news articles

### Technical Features

- **JWT Authentication**: Secure user authentication with token-based sessions
- **Real-time Streaming**: Support for streaming AI responses (optional)
- **Data Persistence**: Chat history and sessions stored in PostgreSQL
- **Rate Limiting Protection**: Optimized image loading to prevent API rate limits
- **Lazy Loading**: Efficient image loading for better performance

## Demo Video

<!-- TODO: Add screen recording video here showing the application features -->
<!-- 
[![TPA Demo](video-thumbnail.png)](demo-video.mp4)
-->

## Tech Stack

### Backend

- **Framework**: FastAPI
- **AI/LLM**: LangGraph with GPT-4o-mini
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt password hashing
- **Migrations**: Alembic
- **External APIs**: SearchAPI.io for flights, hotels, and news
- **Observability**: LangSmith integration (optional)

### Frontend

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **State Management**: React Context API

## Project Structure

```
TPA/
├── src/
│   ├── backend/              # FastAPI backend service
│   │   ├── api/v1/routes/    # API endpoints
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── chat.py       # Chat endpoints
│   │   │   └── data.py       # Data retrieval endpoints
│   │   ├── services/         # Business logic
│   │   │   ├── ai_service.py      # LangGraph agent
│   │   │   ├── flight_service.py  # Flight search
│   │   │   ├── hotel_service.py   # Hotel search
│   │   │   └── news_service.py    # News search
│   │   ├── models/          # Pydantic & SQLAlchemy models
│   │   ├── db/              # Database configuration
│   │   ├── auth/            # Authentication utilities
│   │   └── alembic/         # Database migrations
│   │
│   └── UI/                  # React frontend
│       ├── src/
│       │   ├── components/  # React components
│       │   │   ├── Auth/    # Login/Register
│       │   │   └── Chat/    # Chat interface
│       │   ├── contexts/    # React Context providers
│       │   ├── services/    # API client
│       │   └── App.tsx      # Main app component
│       └── package.json
│
├── docker-compose.yml        # Docker setup
└── README.md                 # This file
```

## Installation

### Prerequisites

- Python 3.13+
- Node.js 18+ and npm
- PostgreSQL 14+
- UV package manager (for Python)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd src/backend
```

2. Install dependencies using UV:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env  # If exists, or create .env file
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tpa_db

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# SearchAPI
SERP_API_KEY=your_searchapi_key

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256

# Optional
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=your_project_name
```

4. Set up the database:
```bash
# Run migrations
alembic upgrade head
```

5. Start the backend server:
```bash
./start.sh
# Or manually:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the UI directory:
```bash
cd src/UI
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file (optional):
```bash
# Create .env file if you need to override API URL
VITE_API_URL=http://localhost:8000/api/v1
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000` (or next available port)

## Usage

### Getting Started

1. **Register/Login**: Create an account or login with existing credentials
2. **Start Chatting**: Type your questions in natural language
3. **Search Flights**: Ask "Find flights from Mumbai to Delhi on December 20"
4. **Search Hotels**: Ask "Good hotels in Goa for 3 nights from tomorrow"
5. **Get News**: Ask "Latest travel news for Japan"
6. **View Details**: Click on hotel cards to see image galleries and booking links

### Example Queries

- "Find flights from New York to London next week"
- "Show me hotels in Bali from Nov 17 to Nov 20"
- "What are good budget hotels in Paris?"
- "Latest travel restrictions for Italy"
- "Hotels near the beach in Goa"

### Chat Features

- **Multiple Sessions**: Create new chat sessions for different topics
- **Session History**: All previous conversations are saved
- **Persistent State**: Sessions and authentication persist across page refreshes
- **Theme Toggle**: Switch between light and dark modes

## API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info

### Chat Endpoints

- `POST /api/v1/chat/` - Send message to AI agent
  - Request body: `{ "message": "user message", "thread_id": "optional" }`
  - Response: `{ "response": "AI response", "thread_id": "...", "data_store": {...} }`

- `GET /api/v1/chat/history/{thread_id}` - Get conversation history
- `DELETE /api/v1/chat/clear-data` - Clear cached data

### Data Endpoints

- `GET /api/v1/data/{data_type}/{key}` - Retrieve specific search results
- `GET /api/v1/data/{data_type}/keys` - List available data keys

### Health Check

- `GET /health` - Service health status
- `GET /` - API information

Full API documentation available at `http://localhost:8000/docs` when the backend is running.

## Development

### Backend Development

```bash
cd src/backend

# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd src/UI

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Code Structure

**Backend**:
- Routes handle HTTP requests and validation
- Services contain business logic and external API calls
- Models define data structures and database schemas
- AI service orchestrates the LangGraph agent

**Frontend**:
- Components are organized by feature (Auth, Chat)
- Contexts manage global state (Auth, Chat, Theme)
- Services handle API communication
- CSS uses CSS variables for theming

## Configuration

### Backend Configuration

Edit `src/backend/services/config.py` or use environment variables to configure:
- API endpoints
- Default search parameters
- Database connection
- Authentication settings

### Frontend Configuration

Edit `src/UI/src/services/api.ts` to configure:
- API base URL
- Request timeouts
- Error handling

## Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User accounts and authentication
- **conversations**: Chat session metadata
- **messages**: Individual chat messages
- LangGraph checkpoints: Stored conversation state

## Security

- JWT tokens for authentication
- Password hashing with bcrypt
- CORS middleware configured
- Environment-based secrets
- SQL injection protection via SQLAlchemy ORM

## Performance Optimizations

- Lazy loading for images
- Thumbnail images to reduce bandwidth
- Limited concurrent image requests
- Efficient data structure (TOON format for LLM, full data for UI)
- Database connection pooling
- Async operations throughout

## Troubleshooting

### Backend Issues

- **Database connection errors**: Check PostgreSQL is running and DATABASE_URL is correct
- **API key errors**: Verify OPENAI_API_KEY and SERP_API_KEY in .env
- **Migration errors**: Run `alembic upgrade head` to sync database schema

### Frontend Issues

- **API connection errors**: Verify backend is running and VITE_API_URL is correct
- **Image loading errors**: Check browser console for 429 rate limit errors (images use lazy loading)
- **Session not persisting**: Check browser localStorage is enabled

### Common Solutions

- Clear browser cache and localStorage if experiencing stale data
- Restart both backend and frontend servers
- Check network tab in browser DevTools for API errors
- Verify all environment variables are set correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Acknowledgments

- Built with FastAPI, React, and LangGraph
- Uses SearchAPI.io for travel data
- Powered by OpenAI GPT-4o-mini

---

For detailed backend documentation, see [src/backend/README.md](src/backend/README.md)

