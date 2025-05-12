# GeoRAG Chat

GeoRAG Chat is an intelligent Q&A system that combines RAG (Retrieval-Augmented Generation) with geospatial database capabilities. It can handle both document queries and geospatial data queries, providing comprehensive information retrieval and Q&A services.

## Features

- **Document Processing**
  - Support for multiple document formats (PDF, TXT, DOCX, JSON)
  - Incremental document processing
  - Real-time processing progress display
  - Efficient vector retrieval using FAISS

- **Geospatial Queries**
  - PostgreSQL database with PostGIS extension
  - Support for complex geospatial queries
  - Multilingual place name search (Chinese, English)
  - Distance calculations and spatial relationship queries

- **User Interface**
  - Modern frosted glass style interface
  - Real-time progress display
  - Responsive design
  - Elegant animations

## System Architecture

https://github.com/user-attachments/assets/0ec38171-00d8-4de6-a92d-93f844aa637a

## System Requirements

- Python 3.8+
- PostgreSQL 13+ with PostGIS
- Modern browser (WebSocket support)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Database_chatpal
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
   - Copy `.env.template` to `.env`
   - Fill in the required configuration:
     ```
     OPENAI_API_KEY=your_openai_api_key
     POSTGRES_USER=your_postgres_user
     POSTGRES_PASSWORD=your_postgres_password
     POSTGRES_HOST=localhost
     POSTGRES_PORT=5432
     POSTGRES_DB=geo_rag_db
     ```

5. Initialize database:
```bash
# Ensure PostgreSQL and PostGIS are installed
# Create database and tables
psql -U your_postgres_user -d geo_rag_db -f init_db.sql
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the application:
   - Open your browser and visit `http://localhost:5000`

3. Upload documents:
   - Click the upload area to select files
   - Supported formats: PDF, TXT, DOCX, JSON
   - Real-time processing progress display

4. Query functionality:
   - Document queries: Ask questions about uploaded documents
   - Geospatial queries: Ask questions about geographical locations
   - Mixed queries: Questions involving both documents and geospatial information

## Example Queries

1. Document queries:
   - "What are the famous attractions in Shanghai?"
   - "What historical buildings are mentioned in the documents?"

2. Geospatial queries:
   - "Which cities are within 100 kilometers of Shanghai?"
   - "Find locations with names containing 'Beijing'"

3. Mixed queries:
   - "What attractions mentioned in the documents are near Shanghai?"
   - "Among the cities mentioned in the documents, which ones are closest to Beijing?"

## Project Structure

```
Database_chatpal/
├── app.py                 # Flask application main file
├── document_processor.py  # Document processing module
├── geo_db_toolkit.py      # Geospatial database tools
├── geo_rag_agent.py       # RAG agent implementation
├── file_upload_handler.py # File upload handling
├── requirements.txt       # Project dependencies
├── .env.template         # Environment variables template
├── init_db.sql           # Database initialization script
└── templates/            # Frontend templates
    └── index.html        # Main page
```

## Development Guide

### Document Processing Workflow

1. File upload:
   - Validate file type
   - Check for existing files
   - Save to docs directory

2. Document processing:
   - Load document content
   - Text splitting
   - Generate vector embeddings
   - Update FAISS index

3. Incremental updates:
   - Process only newly uploaded files
   - Maintain existing vector store
   - Real-time save updates

### Geospatial Queries

1. Query processing:
   - Parse natural language queries
   - Generate SQL statements
   - Execute spatial queries
   - Format results

2. Spatial features:
   - Distance calculations
   - Spatial relationship determination
   - Multilingual place name matching
   - Geocoding

## Important Notes

1. Document processing:
   - Large files may take longer to process
   - Recommended file size under 50MB
   - Supports both Chinese and English documents

2. Database:
   - Ensure PostgreSQL service is running
   - Verify PostGIS extension is properly installed
   - Regular database backups recommended

3. API keys:
   - Securely store OpenAI API key
   - Do not commit keys to version control
   - Regularly update keys

## Troubleshooting

1. Document upload failures:
   - Check if file format is supported
   - Verify file size is within limits
   - Check server logs for detailed error messages

2. No query results:
   - Confirm documents were processed successfully
   - Verify query statement accuracy
   - Check database connection

3. Performance issues:
   - Consider increasing server resources
   - Optimize database indexes
   - Adjust batch processing size

## Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Contact

For questions or suggestions, please submit an Issue or contact the project maintainers.
