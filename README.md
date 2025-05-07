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
- Cursor IDE (for development)
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

#### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/ryoureddy/cardiology-knowledge-graph.git
cd cardiology-knowledge-graph
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
```

4. Configure your API credentials:
   - The project uses a `.env` file for storing API keys and credentials
   - Edit the `.env` file in the project root with your information:
```
# Required for PubMed data acquisition
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your_api_key_here  # Get from https://www.ncbi.nlm.nih.gov/account/settings/

# Neo4j database connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_database_password
```

5. Set up Neo4j database:
   - Install Neo4j Desktop from [https://neo4j.com/download/](https://neo4j.com/download/)
   - Create a new database named "cardiology" with password as configured in your `.env` file
   - Install the APOC plugin
   - Start the database

6. Initialize the database schema:
```bash
python src/database/init_schema.py
```

#### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/ryoureddy/cardiology-knowledge-graph.git
cd cardiology-knowledge-graph
```

2. Create a `.env` file in the project root with your PubMed API credentials:
```
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your_api_key_here
```

3. Build and start the containers:
```bash
docker-compose up -d
```

This will:
- Start a Neo4j container with the APOC plugin installed
- Build and start the Cardiology Knowledge Graph application
- Initialize the database schema automatically

4. Access the application at http://localhost:5000
5. Access Neo4j Browser at http://localhost:7474 (username: neo4j, password: password)

## Project Structure

- `src/data_acquisition/`: Modules for acquiring data from PubMed and medical textbooks
- `src/database/`: Database connection and schema initialization
- `src/processing/`: NLP and data processing modules
- `src/visualization/`: Web interface and graph visualization
- `src/dual_process/`: Implementation of dual process theory views
- `data/`: Raw and processed data storage
- `tests/`: Unit and integration tests

## Usage

To run the web application after setting up:

```bash
# Local installation
python src/visualization/app.py

# Docker installation
# The application starts automatically with docker-compose
```

## Data Acquisition

To acquire cardiology data from PubMed and free textbooks:

```bash
# Fetch data from PubMed
python src/data_acquisition/pubmed_fetcher.py

# Fetch data from free textbooks
python src/data_acquisition/textbook_fetcher.py
```

## Building the Knowledge Graph

After acquiring data, process it and build the knowledge graph:

```bash
# Extract entities
python src/processing/entity_extractor.py

# Extract relationships
python src/processing/relationship_extractor.py

# Build knowledge graph in Neo4j
python src/database/graph_builder.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Medical literature sources (PubMed, OpenStax, etc.)
- Neo4j and py2neo for graph database functionality
- NLP libraries and tools for medical text processing
