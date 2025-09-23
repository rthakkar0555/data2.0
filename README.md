# Manual Retrieval System

A full-stack application for uploading and querying PDF manuals using RAG (Retrieval-Augmented Generation) technology.

## Features

- **Admin Dashboard**: Upload PDF manuals with company and product information
- **User Interface**: Chat with AI assistant to get answers from uploaded manuals
- **Real-time Processing**: Fast PDF processing and vector search
- **Company Management**: Organize manuals by company and product

## Architecture

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, and shadcn/ui components
- **Backend**: FastAPI with Python
- **Vector Database**: Qdrant for document embeddings
- **Database**: MongoDB for metadata storage
- **AI**: NIM AI Support

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd Rag_Manual_retrival/backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the backend directory with:
   ```
   NIM_api_key=nim api key
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB=datquest
   MONGODB_COLLECTION=uploads
   ```

4. Start Qdrant vector database:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

5. Run the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   Create a `.env.local` file in the root directory with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

### Admin Panel
- Access at `/admin` (use email containing "admin" to login)
- Upload PDF manuals with company name, product name, and product code
- View all uploaded manuals and their status
- Monitor system metrics

### User Interface
- Access at `/user` (use any other email to login)
- Select company and product to load specific manual
- Ask questions about the manual content
- Upload new manuals if needed

## API Endpoints

### Backend API (Port 8000)
- `POST /upload_pdf/` - Upload and process PDF
- `POST /query/` - Query the AI assistant
- `GET /companies/` - Get all companies
- `GET /companies/{company}/models/` - Get models for a company
- `GET /health/` - Health check

### Frontend (Port 3000)
- `/` - Redirects to login
- `/login` - Login page
- `/admin` - Admin dashboard
- `/user` - User interface

## Configuration

The backend URL can be configured in `lib/config.ts` or via the `NEXT_PUBLIC_API_URL` environment variable.

## Troubleshooting

1. **Backend not responding**: Check if the backend server is running on port 8000
2. **Qdrant connection failed**: Ensure Qdrant is running on port 6333
3. **MongoDB connection failed**: Verify your MongoDB connection string
4. **OpenAI API errors**: Check your OpenAI API key and credits
5. **Frontend errors**: The app includes error boundaries and better error handling
6. **Test backend connection**: Run `node test-backend.js` to verify backend connectivity

## Error Handling

The application includes comprehensive error handling:
- **Error Boundaries**: Catch React component errors gracefully
- **API Error Handling**: Proper error messages for all API calls
- **Loading States**: Visual feedback during data loading
- **Validation**: File type and size validation for uploads
- **Fallback States**: Graceful degradation when services are unavailable

## Development

- Frontend: Next.js with TypeScript
- Backend: FastAPI with Python
- Styling: Tailwind CSS with shadcn/ui components
- State Management: React hooks
- API Communication: Fetch API with custom service layer
