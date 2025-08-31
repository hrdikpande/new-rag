# Website RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that scrapes website content and answers questions using Google's Gemini AI.

## Features

- **Web Scraping**: Asynchronously scrapes website content with configurable limits
- **Content Processing**: Extracts clean text using readability algorithms
- **Vector Database**: Stores content embeddings in ChromaDB for fast similarity search
- **AI Integration**: Uses Google Gemini for natural language responses
- **Environment Configuration**: All settings managed through environment variables

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Website scraping configuration
SCRAPE_URL=https://your-website-to-scrape.com/
MAX_URLS=1000
CONCURRENCY=10

# Google AI API Configuration (required)
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Database and file paths
SCRAPED_PAGES_DIR=./scraped_pages
CHROMADB_DIR=./chromadb
COLLECTION_NAME=site_documents

# Text processing configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MIN_CHUNK_SIZE=100
```

### 3. Get Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Add it to your `.env` file as `GOOGLE_AI_API_KEY`

## Usage

### Step 1: Scrape Website Content

```bash
python scraper.py
```

This will:
- Discover URLs from your target website
- Scrape and clean the content
- Save text files to the configured directory

### Step 2: Process and Store Embeddings

```bash
python embedding.py
```

This will:
- Load scraped text files
- Create text chunks with overlap
- Generate embeddings using Google AI
- Store in ChromaDB for fast retrieval

### Step 3: Run the Chatbot

```bash
python queryresponse.py
```

This will:
- Start an interactive chat session
- Answer questions based on scraped content
- Use RAG (Retrieval-Augmented Generation) for responses

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPE_URL` | Website to scrape | Required |
| `MAX_URLS` | Maximum URLs to scrape | 1000 |
| `CONCURRENCY` | Concurrent scraping requests | 10 |
| `GOOGLE_AI_API_KEY` | Google AI API key | Required |
| `SCRAPED_PAGES_DIR` | Directory for scraped files | ./scraped_pages |
| `CHROMADB_DIR` | ChromaDB storage directory | ./chromadb |
| `COLLECTION_NAME` | ChromaDB collection name | site_documents |
| `CHUNK_SIZE` | Text chunk size for embeddings | 1000 |
| `CHUNK_OVERLAP` | Overlap between chunks | 200 |
| `MIN_CHUNK_SIZE` | Minimum chunk size to process | 100 |

## File Structure

```
backend/
├── .env                 # Environment configuration
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
├── scraper.py          # Website scraping script
├── embedding.py        # Text processing and embedding storage
├── queryresponse.py    # RAG chatbot interface
├── scraped_pages/      # Scraped content (generated)
└── chromadb/          # Vector database (generated)
```

## Security Notes

- Never commit `.env` files to version control
- Keep your Google AI API key secure
- Add `.env` to your `.gitignore` file

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure `GOOGLE_AI_API_KEY` is set in your `.env` file
2. **Scraping Issues**: Check if the target website allows scraping and adjust `CONCURRENCY`
3. **Memory Issues**: Reduce `CHUNK_SIZE` or `MAX_URLS` for large websites
4. **Empty Responses**: Ensure scraped content is relevant and embeddings are generated

### Debug Mode

For debugging, you can run each script individually and check the output directories.
