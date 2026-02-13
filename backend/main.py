from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Hashable, List, Optional, Any
import sqlite3
import uvicorn
from authenticator import verify_access
from fastapi.middleware.cors import CORSMiddleware
from config import set_env_var
from data_similarity import DataSimilarity, load_toc_structure
import logging

logger = logging.getLogger("uvicorn.error")

from data_handler import (
    init_database, get_ideas, get_idea_from_tags,
    get_content, get_tags, get_tags_from_idea, add_idea, add_tag, 
    add_relation, remove_idea, remove_tag, remove_relation, update_idea, get_similar_idea
)


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
    """Ideam model for idea items with title, content, and tags.
    
    Attributes:
        id (int): The id of the idea.
        title (str): The name of the idea.
        content (str): The description of the idea item.
        tags (Optional[str]): Tags associated with the idea item, 
                             separated by semicolons.
    """
    id: Optional[int] = None
    title: str
    content: str
    tags: Optional[str] = None #tags are semicolon-separated

class TagItem(BaseModel):
    """Data model for tag items.
    
    Attributes:
        name (str): The name of the tag.
    """
    name: str

class RelationItem(BaseModel):
    """Data model for relations between ideas and tags.
    
    Attributes:
        idea_id (int): The id of the idea.
        tag_name (str): The name of the tag.
    """
    idea_id: int
    tag_name: str


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
async def get_all_ideas() -> List[dict[Hashable, Any]]:
    """Get all ideas with optional limit.
    
    Args:
        limit (int, optional): Maximum number of ideas to return. 
                              Defaults to 500.
    
    Returns:
        List[dict[Hashable, Any]]: List of ideas with their details.
    
    Raises:
        HTTPException: If there's an error retrieving data from the database.
    """
    try:
        ideas = get_ideas()
        return ideas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

@app.get("/ideas/tags/{tags}", response_model=List[IdeaItem])
async def get_ideas_by_tags(tags: str) -> List[dict[Hashable, str]]:
    """Get ideas by tags (semicolon separated).
    
    Args:
        tags (str): Tags to filter ideas, separated by semicolons.
    
    Returns:
        List[dict[Hashable, str]]: List of ideas matching the specified tags.
    
    Raises:
        HTTPException: If there's an error retrieving data from the database.
    """
    try:
        ideas = get_idea_from_tags(tags)
        return ideas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data by tags: {str(e)}")

@app.get("/ideas/search/{subname}", response_model=List[IdeaItem])
async def search_ideas(subname: str) -> List[dict[Hashable, Any]]:
    """Search ideas by partial name.
    
    Args:
        subname (str): Partial name to search for in ideas.
    
    Returns:
        List[dict[Hashable, Any]]: List of ideas matching the search term.
    
    Raises:
        HTTPException: If there's an error searching data in the database.
    """
    try:
        data = get_similar_idea(subname)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching data: {str(e)}")

@app.get("/ideas/{idea_id}/content", response_model=str)
async def get_idea_content(idea_id: int) -> str:
    """Get content of a specific idea.
    
    Args:
        idea_id (int): The ID of the idea to retrieve content for.
    
    Returns:
        str: The content of the specified idea.
    
    Raises:
        HTTPException: If there's an error retrieving the content from the database.
    """
    try:
        content = get_content(idea_id)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving content: {str(e)}")

@app.get("/tags", response_model=List[TagItem])
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

@app.get("/ideas/{idea_id}/tags", response_model=List[str])
async def get_tags_for_idea(idea_id: int):
    """Get tags for a specific idea.
    
    Args:
        idea_id (int): The id of the idea to retrieve tags for.
    
    Returns:
        List[str]: List of tags associated with the specified idea.
    
    Raises:
        HTTPException: If there's an error retrieving tags from the database.
    """
    try:
        tags = get_tags_from_idea(idea_id)
        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tags for data: {str(e)}")

@app.get("/ideas/similar/{idea}", response_model=List[IdeaItem])
async def get_similar_ideas_endpoint(idea: str):
    """Get similar ideas based on semantic similarity.
    
    Args:
        idea (str): The name of the idea to find similar items for.
    
    Returns:
        List[IdeaItem]: List of similar ideas based on semantic similarity.
    
    Raises:
        HTTPException: If the idea is not found or there's an error 
                      retrieving similar data.
    """
    try:
        # Call the original function to get similar data
        similar_data = get_similar_idea(idea)
        return similar_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving similar ideas: {str(e)}")

# POST endpoints
@app.post("/ideas", response_model=dict)
async def create_idea(data: IdeaItem) -> dict[str, str | int]:
    """Add a new idea item.
    
    Args:
        idea (IdeaItem): The idea item data to add, including title, content, and optional tags.
    
    Returns:
        dict[str, str]: A success message indicating the idea item was added.
    
    Raises:
        HTTPException: If there's an error adding the data to the database.
    """
    try:
        new_id = add_idea(data.title, data.content, owner=1)  # Assuming owner_id = 1 for now
        
        # Handle tags if provided - convert string to list if needed
        if data.tags and data.tags.strip():
            # Split the semicolon-separated string into individual tags
            tags_list = [tag.strip() for tag in data.tags.split(';') if tag.strip()]
            for tag in tags_list:
                try:
                    add_tag(tag)
                    add_relation(new_id, tag)
                except Exception as e:
                    # Continue processing other tags even if one fails
                    logger.info(f"Warning: Failed to process tag '{tag}': {str(e)}")
        
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding idea: {str(e)}")

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
        add_relation(relation.idea_id, relation.tag_name)
        return {"message": f"Relation between '{relation.idea_id}' and '{relation.tag_name}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating relation: {str(e)}")

# PUT endpoint
@app.put("/ideas/{id}", response_model=dict)
async def update_idea_item(id: int, idea: IdeaItem) -> dict[str, str]:
    """Update an existing idea.
    
    Args:
        id (int): the idea id
        idea (IdeaItem): The updated idea information including title, content, and optional tags.
    
    Returns:
        dict[str, str]: A success message indicating the idea was updated.
    
    Raises:
        HTTPException: If there's an error updating the data in the database.
    """
    try:
        update_idea(id=id, title=idea.title, content=idea.content)
        if idea.tags and idea.tags.strip():
            # Split the semicolon-separated string into individual tags
            tags_list = [tag.strip() for tag in idea.tags.split(';') if tag.strip()]
            
            # Get current tags for this idea
            current_tags = get_tags_from_idea(id)
            
            # Convert current tags to set for easy comparison
            current_tags_set = set(current_tags)
            
            # Convert new tags to set for easy comparison
            new_tags_set = set(tags_list)
            
            # Find tags to remove (current tags not in new tags)
            tags_to_remove = current_tags_set - new_tags_set
            
            # Find tags to add (new tags not in current tags)
            tags_to_add = new_tags_set - current_tags_set
            
            # Remove obsolete relations (tags that existed before but are not in new tags)
            for tag in tags_to_remove:
                try:
                    remove_relation(id, tag)
                except Exception as e:
                    logger.info(f"Warning: Failed to remove relation for tag '{tag}': {str(e)}")
            
            # Add new relations (tags that are in new tags but didn't exist before)
            for tag in tags_to_add:
                try:
                    add_tag(tag)
                    add_relation(id, tag)
                except Exception as e:
                    # Continue processing other tags even if one fails
                    logger.info(f"Warning: Failed to process tag '{tag}': {str(e)}")
        return {"message": f"Idea '{id}' updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating idea: {str(e)}")

# DELETE endpoints
@app.delete("/ideas/{id}", response_model=dict)
async def delete_idea(id: int, idea: IdeaItem) -> dict[str, str]:
    """Remove a idea.
    
    Args:
        id (int): The id of the idea to remove.
        idea (IdeaItem): The idea information including title, content, and optional tags.
    
    Returns:
        dict[str, str]: A success message indicating the idea was removed.
    
    Raises:
        HTTPException: If there's an error removing the data from the database.
    """
    try:
        remove_idea(id=id, title=idea.title)
        return {"message": f"Idea '{id}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing idea: {str(e)}")

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
        relation (RelationItem): The relationship data containing idea id and tag name.
    
    Returns:
        dict[str, str]: A success message indicating the relationship was removed.
    
    Raises:
        HTTPException: If there's an error removing the relationship from the database.
    """
    try:
        remove_relation(relation.idea_id, relation.tag_name)
        return {"message": f"Relation between '{relation.idea_id}' and '{relation.tag_name}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing relation: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}

# TOC endpoint
@app.get("/toc/structure", response_model=list)
async def get_toc_structure() -> list:
    """Get hierarchical table of contents structure from all data.
    
    Returns:
        list: Hierarchical table of contents structure generated from all data.
    
    Raises:
        HTTPException: If there's an error generating the TOC structure.
    """
    
    try:
        toc = None
        toc =  load_toc_structure()
        if toc: 
            return toc
        else: 
            data_similarity = DataSimilarity()
            return data_similarity.generate_toc_structure()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TOC structure: {str(e)}")
    
@app.post("/toc/update", response_model=dict)
async def update_toc_structure() -> dict[str, str]:
    """Update the hierarchical table of contents structure
    
    Returns:
        list: Hierarchical table of contents structure generated from all data.
    
    Raises:
        HTTPException: If there's an error updating the toc.
    """
    try:
        data_similarity = DataSimilarity()
        data_similarity.generate_toc_structure()
        return {"message": f"toc added successfully"}
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
    # Initialize the database
    set_env_var()
    init_database()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)