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

### Installation

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

4. Set up Neo4j database:
   - Install Neo4j Desktop from [https://neo4j.com/download/](https://neo4j.com/download/)
   - Create a new database named "cardiology" with password "password" (change for production)
   - Install the APOC plugin
   - Start the database

5. Initialize the database schema:
```bash
python src/database/init_schema.py
```

## Project Structure

- `src/data_acquisition/`: Modules for acquiring data from PubMed and medical textbooks
- `src/database/`: Database connection and schema initialization
- `src/processing/`: NLP and data processing modules
- `src/visualization/`: Web interface and graph visualization
- `src/dual_process/`: Implementation of dual process theory views
- `data/`: Raw and processed data storage
- `tests/`: Unit and integration tests

## Usage

[Usage instructions will be added as the project progresses]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Medical literature sources (PubMed, OpenStax, etc.)
- Neo4j and py2neo for graph database functionality
- NLP libraries and tools for medical text processing 