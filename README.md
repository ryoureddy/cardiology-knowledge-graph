# Cardiology Knowledge Graph System

A knowledge graph system that integrates dual process theory to enhance cardiology medical education. This project focuses on building a comprehensive knowledge graph for cardiology data, making connections between conditions, treatments, anatomy, procedures, and other medical concepts.

## Features

- Automated data acquisition from medical literature (PubMed) and free medical textbooks
- Neo4j graph database for storing and querying complex relationships
- Natural language processing to extract medical entities and relationships
- Web interface for exploring the cardiology knowledge graph
- Dual process theory integration for intuitive (System 1) and analytical (System 2) learning modes

## Getting Started

### Prerequisites

- Python 3.8 or later
- Neo4j Desktop (latest version)
- Docker and Docker Compose (for containerized setup)

### Setup

#### Option 1: Running with Docker (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/ryoureddy/cardiology-knowledge-graph.git
   cd cardiology-knowledge-graph
   ```

2. Create a `.env` file in the project root with your PubMed API credentials and Neo4j settings:
   ```
   # Cardiology Knowledge Graph environment variables

   # NCBI/PubMed API credentials
   PUBMED_EMAIL=your.email@example.com
   PUBMED_API_KEY=your_api_key_here

   # Neo4j database connection (these settings are used for local development only)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

4. Access the application and Neo4j browser:
   - Cardiology Knowledge Graph: http://localhost:5001/
   - Neo4j Browser: http://localhost:7474/ (connect with username: neo4j, password: password)

#### Option 2: Running Locally

1. Clone the repository:
   ```
   git clone https://github.com/ryoureddy/cardiology-knowledge-graph.git
   cd cardiology-knowledge-graph
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   python -m nltk.downloader punkt stopwords
   ```

3. Create a `.env` file in the project root with your PubMed API credentials and Neo4j settings:
   ```
   # Cardiology Knowledge Graph environment variables

   # NCBI/PubMed API credentials
   PUBMED_EMAIL=your.email@example.com
   PUBMED_API_KEY=your_api_key_here

   # Neo4j database connection
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

4. Ensure Neo4j is running and initialize the database schema:
   ```
   python src/database/init_schema.py
   ```

5. Run the Flask application:
   ```
   export FLASK_APP=src/visualization/app.py
   flask run
   ```

## Usage

### Data Acquisition

The system automatically fetches cardiology-related data from:
- PubMed research articles
- Medical textbooks (currently focusing on openly available cardiology content)

To manually trigger data acquisition:
```
python src/data_acquisition/run_acquisition.py
```

### Knowledge Graph Building

After data acquisition, the graph is constructed by:
1. Extracting medical entities (conditions, treatments, etc.)
2. Identifying relationships between entities
3. Populating the Neo4j database

To manually rebuild the knowledge graph:
```
python src/database/build_graph.py
```

### Dual Process Views

The system supports three different views:
- **Complete View**: Shows the entire knowledge graph
- **System 1 View**: Focuses on intuitive, pattern-recognition aspects for quick reference
- **System 2 View**: Highlights analytical, detailed reasoning connections

## Project Structure

```
cardiology-knowledge-graph/
├── data/
│   ├── raw/             # Raw data from PubMed and textbooks
│   └── processed/       # Extracted entities and relationships
├── src/
│   ├── data_acquisition/  # PubMed and textbook data fetching
│   ├── processing/        # NLP and entity/relationship extraction
│   ├── database/          # Neo4j database operations
│   ├── dual_process/      # System 1 and System 2 view generation
│   └── visualization/     # Flask web application
└── requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Medical literature sources (PubMed, OpenStax, etc.)
- Neo4j and py2neo for graph database functionality
- NLP libraries and tools for medical text processing
