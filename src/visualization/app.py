"""
Flask application for the Cardiology Knowledge Graph visualization interface.
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
import logging
import os
import json
from pathlib import Path
import sys

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.dual_process.view_generator import DualProcessViews

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder=os.path.join(project_root, "src", "visualization", "static"),
            template_folder=os.path.join(project_root, "src", "visualization", "templates"))

# Initialize the dual process views generator
views = DualProcessViews()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/api/search', methods=['GET'])
def search_entities():
    """
    API endpoint to search for entities.
    
    Query Parameters:
        q (str): Search term
        limit (int): Maximum number of results (default: 10)
    """
    search_term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not search_term or len(search_term) < 2:
        return jsonify({'results': []})
    
    try:
        results = views.search_entities(search_term, limit)
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error searching entities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entity/<entity_name>', methods=['GET'])
def get_entity_info(entity_name):
    """
    API endpoint to get entity information.
    
    Path Parameters:
        entity_name (str): Name of the entity
    
    Query Parameters:
        type (str): Entity type (optional)
    """
    entity_type = request.args.get('type', None)
    
    try:
        info = views.get_entity_info(entity_name, entity_type)
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting entity info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/view/<view_type>/<entity_name>', methods=['GET'])
def get_graph_view(view_type, entity_name):
    """
    API endpoint to get a graph view.
    
    Path Parameters:
        view_type (str): Type of view (system1, system2, complete)
        entity_name (str): Name of the entity
    
    Query Parameters:
        type (str): Entity type (optional)
        limit (int): Maximum number of relationships (default: 50)
    """
    entity_type = request.args.get('type', None)
    limit = request.args.get('limit', 50, type=int)
    
    try:
        if view_type == 'system1':
            view = views.generate_system1_view(entity_name, entity_type, limit)
        elif view_type == 'system2':
            view = views.generate_system2_view(entity_name, entity_type, limit)
        elif view_type == 'complete':
            view = views.generate_complete_view(entity_name, entity_type, limit)
        else:
            return jsonify({'error': f"Invalid view type: {view_type}"}), 400
        
        return jsonify(view)
    except Exception as e:
        logger.error(f"Error generating view: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/entity/<entity_name>')
def entity_detail(entity_name):
    """Render the entity detail page."""
    return render_template('entity.html', entity_name=entity_name)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True) 