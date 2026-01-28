from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Hashable, List, Optional, Any
import sqlite3
import uvicorn
from authenticator import verify_access
from fastapi.middleware.cors import CORSMiddleware
from config import NAME_DB
from data_similarity import DataSimilarity

from data_handler import (
    init_database, get_data, get_data_from_tags, get_selected_data, 
    get_description, get_tags, get_tags_from_data, add_data, add_tag, 
    add_relation, remove_data, remove_tag, remove_relation, update_data, get_similar_data
)


# Initialize the database
init_database()

app = FastAPI(title="Data Management API", description="API for managing data and tags with SQLite")

# Add CORS middleware
# Explicitly allow only trusted origins
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://pierreseroul.com",
    "http://pierreseroul.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class IdeaItem(BaseModel):
    """Data model for idea items with name, description, and tags.
    
    Attributes:
        name (str): The name of the idea item.
        description (str): The description of the idea item.
        tags (Optional[str]): Tags associated with the idea item, 
                             separated by semicolons.
    """
    name: str
    description: str
    tags: Optional[str] = None #tags are semicolon-separated

class TagItem(BaseModel):
    """Data model for tag items.
    
    Attributes:
        name (str): The name of the tag.
    """
    name: str

class RelationItem(BaseModel):
    """Data model for relations between data items and tags.
    
    Attributes:
        data_name (str): The name of the data item.
        tag_name (str): The name of the tag.
    """
    data_name: str
    tag_name: str

class TagResponse(BaseModel):
    """Data model for tag responses.
    
    Attributes:
        name (str): The name of the tag.
    """
    name: str

class LoginRequest(BaseModel):
    """Data model for login requests with email and OTP code.
    
    Attributes:
        email (str): The user's email address.
        otp_code (str): The one-time password code for verification.
    """
    email: str
    otp_code: str

# Helper function to get database connection
def get_db():
    """Get a database connection for SQLite operations.
    
    This function creates a connection to the SQLite database and yields it
    for use in database operations. The connection is automatically closed
    after use.
    
    Yields:
        sqlite3.Connection: A SQLite database connection object.
    """
    conn = sqlite3.connect(NAME_DB)
    yield conn
    conn.close()

# GET endpoints
@app.get("/ideas", response_model=List[IdeaItem])
async def get_all_data(limit: int = 500) -> List[dict[Hashable, Any]]:
    """Get all data items with optional limit.
    
    Args:
        limit (int, optional): Maximum number of data items to return. 
                              Defaults to 500.
    
    Returns:
        List[dict[Hashable, Any]]: List of data items with their details.
    
    Raises:
        HTTPException: If there's an error retrieving data from the database.
    """
    try:
        data = get_data(limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

@app.get("/ideas/tags/{tags}", response_model=List[IdeaItem])
async def get_data_by_tags(tags: str, limit: int = 500) -> List[dict[Hashable, str]]:
    """Get data items by tags (semicolon separated).
    
    Args:
        tags (str): Tags to filter data items, separated by semicolons.
        limit (int, optional): Maximum number of data items to return. 
                              Defaults to 500.
    
    Returns:
        List[dict[Hashable, str]]: List of data items matching the specified tags.
    
    Raises:
        HTTPException: If there's an error retrieving data from the database.
    """
    try:
        data = get_data_from_tags(tags, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data by tags: {str(e)}")

@app.get("/ideas/search/{subname}", response_model=List[IdeaItem])
async def search_data(subname: str) -> List[dict[Hashable, Any]]:
    """Search data items by partial name.
    
    Args:
        subname (str): Partial name to search for in data items.
    
    Returns:
        List[dict[Hashable, Any]]: List of data items matching the search term.
    
    Raises:
        HTTPException: If there's an error searching data in the database.
    """
    try:
        data = get_selected_data(subname)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching data: {str(e)}")

@app.get("/ideas/{name}/description", response_model=str)
async def get_data_description(name: str) -> str:
    """Get description of a specific data item.
    
    Args:
        name (str): The name of the data item to retrieve description for.
    
    Returns:
        str: The description of the specified data item.
    
    Raises:
        HTTPException: If there's an error retrieving the description from the database.
    """
    try:
        description = get_description(name)
        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving description: {str(e)}")

@app.get("/tags", response_model=List[TagResponse])
async def get_all_tags() -> List[dict[Hashable, Any]]:
    """Get all tags.
    
    Returns:
        List[dict[Hashable, Any]]: List of all tags in the system.
    
    Raises:
        HTTPException: If there's an error retrieving tags from the database.
    """
    try:
        tags = get_tags()
        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tags: {str(e)}")

@app.get("/ideas/{data_name}/tags", response_model=List[str])
async def get_tags_for_data(data_name: str):
    """Get tags for a specific data item.
    
    Args:
        data_name (str): The name of the data item to retrieve tags for.
    
    Returns:
        List[str]: List of tags associated with the specified data item.
    
    Raises:
        HTTPException: If there's an error retrieving tags from the database.
    """
    try:
        tags = get_tags_from_data(data_name)
        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tags for data: {str(e)}")

@app.get("/data/{data_name}/similar", response_model=List[IdeaItem])
async def get_similar_data_endpoint(data_name: str):
    """Get similar data items based on semantic similarity.
    
    Args:
        data_name (str): The name of the data item to find similar items for.
    
    Returns:
        List[IdeaItem]: List of similar data items based on semantic similarity.
    
    Raises:
        HTTPException: If the data item is not found or there's an error 
                      retrieving similar data.
    """
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
    """Add a new idea item.
    
    Args:
        data (IdeaItem): The idea item data to add, including name, description, and optional tags.
    
    Returns:
        dict[str, str]: A success message indicating the idea item was added.
    
    Raises:
        HTTPException: If there's an error adding the data to the database.
    """
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
    """Add a new tag.
    
    Args:
        tag (TagItem): The tag data to add.
    
    Returns:
        dict[str, str]: A success message indicating the tag was added.
    
    Raises:
        HTTPException: If there's an error adding the tag to the database.
    """
    try:
        add_tag(tag.name)
        return {"message": f"Tag '{tag.name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding tag: {str(e)}")

@app.post("/relations", response_model=dict)
async def create_relation(relation: RelationItem) -> dict[str, str]:
    """Create a relationship between data and tag.
    
    Args:
        relation (RelationItem): The relationship data containing data name and tag name.
    
    Returns:
        dict[str, str]: A success message indicating the relationship was created.
    
    Raises:
        HTTPException: If there's an error creating the relationship in the database.
    """
    try:
        add_relation(relation.data_name, relation.tag_name)
        return {"message": f"Relation between '{relation.data_name}' and '{relation.tag_name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating relation: {str(e)}")

# PUT endpoint
@app.put("/ideas/{name}", response_model=dict)
async def update_data_item(name: str, data: IdeaItem) -> dict[str, str]:
    """Update an existing data item.
    
    Args:
        name (str): The name of the data item to update.
        data (IdeaItem): The updated data item information including name, description, and optional tags.
    
    Returns:
        dict[str, str]: A success message indicating the data item was updated.
    
    Raises:
        HTTPException: If there's an error updating the data in the database.
    """
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
    """Remove a data item.
    
    Args:
        name (str): The name of the data item to remove.
    
    Returns:
        dict[str, str]: A success message indicating the data item was removed.
    
    Raises:
        HTTPException: If there's an error removing the data from the database.
    """
    try:
        remove_data(name)
        return {"message": f"Data '{name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing data: {str(e)}")

@app.delete("/tags/{name}", response_model=dict)
async def delete_tag(name: str) -> dict[str, str]:
    """Remove a tag.
    
    Args:
        name (str): The name of the tag to remove.
    
    Returns:
        dict[str, str]: A success message indicating the tag was removed.
    
    Raises:
        HTTPException: If there's an error removing the tag from the database.
    """
    try:
        remove_tag(name)
        return {"message": f"Tag '{name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing tag: {str(e)}")

@app.delete("/relations", response_model=dict)
async def delete_relation(relation: RelationItem) -> dict[str, str]:
    """Remove a relationship between data and tag.
    
    Args:
        relation (RelationItem): The relationship data containing data name and tag name.
    
    Returns:
        dict[str, str]: A success message indicating the relationship was removed.
    
    Raises:
        HTTPException: If there's an error removing the relationship from the database.
    """
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
    """Generate hierarchical table of contents structure from all data.
    
    Args:
        max_items (int, optional): Maximum number of items to include in the TOC. 
                                  Defaults to 500.
    
    Returns:
        list: Hierarchical table of contents structure generated from all data.
    
    Raises:
        HTTPException: If there's an error generating the TOC structure.
    """
    try:
        data_similarity = DataSimilarity()
        toc = data_similarity.generate_toc_structure(max_items)
        return toc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TOC structure: {str(e)}")

@app.post("/verify-otp")
def verify_otp(request: LoginRequest) -> dict[str, str]:
    """Verify the OTP code sent by React.
    
    Args:
        request (LoginRequest): The login request containing email and OTP code.
    
    Returns:
        dict[str, str]: A success response with status and message if verification passes.
    
    Raises:
        HTTPException: If the OTP code is invalid or expired.
    """
    # Check the 6-digit code
    if verify_access(request.email, request.otp_code):
        return {"status": "success", "message": "Connection authorized"}
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired code")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)