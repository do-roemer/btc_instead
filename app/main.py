from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List


app = FastAPI()

# Pydantic model for request body (data validation)
class ResourceCreate(BaseModel):
    name: str
    value: str

# Pydantic model for response (ensures consistent output)
class ResourceResponse(BaseModel):
    id: int
    name: str
    value: str

    class Config:
        orm_mode = True # Allows direct mapping from SQLAlchemy model

@app.post("/resources/", response_model=ResourceResponse, status_code=201)
def create_resource(resource: ResourceCreate, db: Session = Depends(get_db)):
    db_resource = models.Resource(name=resource.name, value=resource.value)
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@app.get("/resources/", response_model=List[ResourceResponse])
def read_resources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    resources = db.query(models.Resource).offset(skip).limit(limit).all()
    return resources

@app.get("/resources/{resource_id}", response_model=ResourceResponse)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return db_resource

# Add more endpoints as needed (PUT for update, DELETE for delete)