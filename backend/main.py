from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Hashable, List, Optional, Any
import sqlite3
import uvicorn
import json
import pyotp
from config import SERVER_DB
from fastapi.middleware.cors import CORSMiddleware

from data_handler import (
    init_database, get_data, get_data_from_tags, get_selected_data, 
    get_description, get_tags, get_tags_from_data, add_data, add_tag, 
    add_relation, remove_data, remove_tag, remove_relation, update_data, get_similar_data
)
from config import NAME_DB
from data_similarity import DataSimilarity

# Initialize the database
init_database()

app = FastAPI(title="Data Management API", description="API for managing data and tags with SQLite")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8050",
                   "http://127.0.0.1:8050",
                   "http://localhost:5173",
                   "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class IdeaItem(BaseModel):
    name: str
    description: str
    tags: Optional[str] = None #tags are semicolon-separated

class TagItem(BaseModel):
    name: str

class RelationItem(BaseModel):
    data_name: str
    tag_name: str

class TagResponse(BaseModel):
    name: str

class LoginRequest(BaseModel):
    email: str
    otp_code: str

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect(NAME_DB)
    yield conn
    conn.close()

# GET endpoints
@app.get("/ideas", response_model=List[IdeaItem])
async def get_all_data(limit: int = 500) -> List[dict[Hashable, Any]]:
    """Get all data items with optional limit"""
    try:
        data = get_data(limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

@app.get("/ideas/tags/{tags}", response_model=List[IdeaItem])
async def get_data_by_tags(tags: str, limit: int = 500) -> List[dict[Hashable, str]]:
    """Get data items by tags (semicolon separated)"""
    try:
        data = get_data_from_tags(tags, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data by tags: {str(e)}")

@app.get("/ideas/search/{subname}", response_model=List[IdeaItem])
async def search_data(subname: str) -> List[dict[Hashable, Any]]:
    """Search data items by partial name"""
    try:
        data = get_selected_data(subname)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching data: {str(e)}")

@app.get("/ideas/{name}/description", response_model=str)
async def get_data_description(name: str) -> str:
    """Get description of a specific data item"""
    try:
        description = get_description(name)
        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving description: {str(e)}")

@app.get("/tags", response_model=List[TagResponse])
async def get_all_tags() -> List[dict[Hashable, Any]]:
    """Get all tags"""
    try:
        tags = get_tags()
        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tags: {str(e)}")

@app.get("/ideas/{data_name}/tags", response_model=List[str])
async def get_tags_for_data(data_name: str):
    """Get tags for a specific data item"""
    try:
        tags = get_tags_from_data(data_name)
        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tags for data: {str(e)}")

@app.get("/data/{data_name}/similar", response_model=List[IdeaItem])
async def get_similar_data_endpoint(data_name: str):
    """Get similar data items based on semantic similarity"""
    try:
        # We need to get the data item first to get its description
        data_item = get_data_from_tags(data_name, limit=1)
        if not data_item:
            raise HTTPException(status_code=404, detail=f"Data item '{data_name}' not found")
        
        # Call the original function to get similar data
        similar_data = get_similar_data(data_name)
        return similar_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving similar data: {str(e)}")

# POST endpoints
@app.post("/ideas", response_model=dict)
async def create_idea(data: IdeaItem) -> dict[str, str]:
    """Add a new idea item"""
    try:
        add_data(data.name, data.description)
        
        # Handle tags if provided - convert string to list if needed
        if data.tags and data.tags.strip():
            # Split the semicolon-separated string into individual tags
            tags_list = [tag.strip() for tag in data.tags.split(';') if tag.strip()]
            for tag in tags_list:
                try:
                    add_tag(tag)
                    add_relation(data.name, tag)
                except Exception as e:
                    # Continue processing other tags even if one fails
                    print(f"Warning: Failed to process tag '{tag}': {str(e)}")
        
        return {"message": f"Data '{data.name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding data: {str(e)}")

@app.post("/tags", response_model=dict)
async def create_tag(tag: TagItem) -> dict[str, str]:
    """Add a new tag"""
    try:
        add_tag(tag.name)
        return {"message": f"Tag '{tag.name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding tag: {str(e)}")

@app.post("/relations", response_model=dict)
async def create_relation(relation: RelationItem) -> dict[str, str]:
    """Create a relationship between data and tag"""
    try:
        add_relation(relation.data_name, relation.tag_name)
        return {"message": f"Relation between '{relation.data_name}' and '{relation.tag_name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating relation: {str(e)}")

# PUT endpoint
@app.put("/ideas/{name}", response_model=dict)
async def update_data_item(name: str, data: IdeaItem) -> dict[str, str]:
    """Update an existing data item"""
    try:
        print("udpate:", name, data.description)
        update_data(name, data.description)
        if data.tags and data.tags.strip():
            # Split the semicolon-separated string into individual tags
            tags_list = [tag.strip() for tag in data.tags.split(';') if tag.strip()]
            for tag in tags_list:
                try:
                    add_tag(tag)
                    add_relation(data.name, tag)
                except Exception as e:
                    # Continue processing other tags even if one fails
                    print(f"Warning: Failed to process tag '{tag}': {str(e)}")
        return {"message": f"Data '{name}' updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data: {str(e)}")

# DELETE endpoints
@app.delete("/ideas/{name}", response_model=dict)
async def delete_data(name: str) -> dict[str, str]:
    """Remove a data item"""
    try:
        remove_data(name)
        return {"message": f"Data '{name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing data: {str(e)}")

@app.delete("/tags/{name}", response_model=dict)
async def delete_tag(name: str) -> dict[str, str]:
    """Remove a tag"""
    try:
        remove_tag(name)
        return {"message": f"Tag '{name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing tag: {str(e)}")

@app.delete("/relations", response_model=dict)
async def delete_relation(relation: RelationItem) -> dict[str, str]:
    """Remove a relationship between data and tag"""
    try:
        remove_relation(relation.data_name, relation.tag_name)
        return {"message": f"Relation between '{relation.data_name}' and '{relation.tag_name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing relation: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}

# TOC endpoint
@app.get("/toc/structure", response_model=list)
async def generate_toc_structure(max_items: int = 500) -> list:
    """Generate hierarchical table of contents structure from all data"""
    try:
        data_similarity = DataSimilarity()
        toc = data_similarity.generate_toc_structure(max_items)
        return toc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TOC structure: {str(e)}")

@app.get("/setup-otp")
def setup_otp() -> dict[str, Any]:
    """
    Étape de configuration : génère l'URL pour Google Authenticator.
    Tu peux copier ce lien dans un générateur de QR Code.
    """
    with open(SERVER_DB, "r") as f:
        server = json.load(f)
    
    secret_key = server['secret_key']
    totp = pyotp.TOTP(secret_key)
    # Crée l'URL que l'application Google Authenticator peut lire
    provisioning_url = totp.provisioning_uri(name="VirtualBrain", issuer_name="RaspberryPi")
    return {"url": provisioning_url, "secret": secret_key}

@app.post("/verify-otp")
def verify_otp(request: LoginRequest) -> dict[str, str]:
    """
    Vérifie si le code envoyé par React est valide.
    """
    with open(SERVER_DB, "r") as f:
        server = json.load(f)
    
    secret_key = server['secret_key']
    totp = pyotp.TOTP(secret_key)
    
    # Vérifie le code à 6 chiffres
    if totp.verify(request.otp_code):
        return {"status": "success", "message": "Connexion autorisée"}
    else:
        raise HTTPException(status_code=401, detail="Code invalide ou expiré")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)