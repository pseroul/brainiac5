# Idea Management API

A FastAPI backend that provides REST endpoints for managing data and tags with SQLite database.

## Features

- Full CRUD operations for data items and tags
- Tag-based filtering and searching
- Relationship management between data and tags
- Semantic similarity support (via ChromaClient)
- Health check endpoint

## Endpoints

### GET Endpoints

- `GET /ideas` - Get all data items (with optional limit)
- `GET /ideas/tags/{tags}` - Get data items by tags (semicolon separated)
- `GET /ideas/search/{subname}` - Search data items by partial name
- `GET /ideas/{name}/description` - Get description of a specific data item
- `GET /tags` - Get all tags
- `GET /ideas/{data_name}/tags` - Get tags for a specific data item
- `GET /health` - Health check endpoint

### POST Endpoints

- `POST /ideas` - Add a new data item
- `POST /tags` - Add a new tag
- `POST /relations` - Create a relationship between data and tag

### PUT Endpoint

- `PUT /ideas/{name}` - Update an existing data item

### DELETE Endpoints

- `DELETE /ideas/{name}` - Remove a data item
- `DELETE /tags/{name}` - Remove a tag
- `DELETE /relations` - Remove a relationship between data and tag

## Data Models

### DataItem
```json
{
  "name": "string",
  "description": "string",
  "tags": "string" (optional)
}
```

### TagItem
```json
{
  "name": "string"
}
```

### RelationItem
```json
{
  "data_name": "string",
  "tag_name": "string"
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
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
- `data` table: stores data items with descriptions
- `relation` table: manages many-to-many relationships between data and tags

