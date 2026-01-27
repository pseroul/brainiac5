# Brainiac5 FastAPI

A FastAPI backend that provides REST endpoints for managing ideas and tags with SQLite database.

## Features

- Full CRUD operations for idea items and tags
- Tag-based filtering and searching
- Relationship management between data and tags
- Semantic similarity support (via ChromaClient)
- Health check endpoint

## Setup

1. Install dependencies:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Generate server secret key
Create a file called ```data/server.json``` and fill it with this model (change the secret_key):`
``` bash
{
    "secret_key" : "my_very_secret_server_key"
}
```

2. Run the server (for debug purpose):
```bash
python main.py
```

3. Access the API at `http://localhost:8000`

4. Access API documentation at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Database

The application uses SQLite with the database file located at `data/knowledge.db`. The database schema includes:

- `tags` table: stores tag information
- `ideas` table: stores idea items with descriptions
- `relation` table: manages many-to-many relationships between ideas and tags


## Toolset
The backend is provided with some tools that helps migrating from a version to another. 

### Update embeddings
If you change your embedding model, a script is provided to update the chromadb with the new embeddings without modifying the sqlite database. 

Simply run the following script: 
```bash
python data_handler.py -e
```

### Clean database
If you want to remove space at the beginning or the end of idea and tags, run the following command: 
```bash
python cleandb.py
```
