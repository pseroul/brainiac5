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

> Depending on your server (aka Raspberry Pi 4 in my case), your code may generate the output `Illegal Instruction`. In this case, try to install an older version on pytorch. In the case of Raspberry Pi 4 - aarch64, the command `pip install torch==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu` worked.

2. Generate secret key:
In order to generate an OTP key to access the server, run the command:
``` bash
python authenticator.py [your_email] 
```
It will display a code that you can put in your Google Auth smartphone app. The bundle ***email / otp_secret*** will be saved in `data/users.json`.

2. Run the server (for debug purpose):
```bash
python main.py
```

3. Access the API at `http://localhost:8000`

4. Access API documentation at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## site configuration
In order to access your fastapi, you need to defined where it is available from. 
Create a ```site.json``` file in *backend/data* and past the following information: 
```
{
    "origins" : [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://[your_site].com",
    "http://[your_site].com"
   ]
}
```
where localhost are used for direct access (aka for debuging) and your site is the domain you use in production.

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
