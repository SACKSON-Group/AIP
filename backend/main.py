from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Query  # Add this line
from typing import List
from typing import Optional  # Add this line
from pydantic import BaseModel
from database import get_db, engine, Base
from models import Project as ProjectModel
from schemas import ProjectCreate, Project
from models import User
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer  # Add this line# Add this line
from models import User
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200")
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)
from datetime import timedelta, datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = "your-secret-key"  # Use env var in prod
ALGORITHM = "HS256"

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return current_user
app = FastAPI()

Base.metadata.create_all(bind=engine)

class AdminReview(BaseModel):
    notes: Optional[str] = None
    approved: bool

@app.post("/projects/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = ProjectModel(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects/")
def read_projects(
        sector: Optional[str] = Query(None),
        country: Optional[str] = Query(None),
        verification_level: Optional[int] = Query(None),
        min_score: Optional[float] = Query(None),
        sort: Optional[str] = Query("bankability_score desc"),
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db)
):
    # Function body with proper indentation
    query = db.query(Project)

    # Existing filters...
    if sector:
        query = query.filter(Project.sector.ilike(f"%{sector}%"))
    if country:
        query = query.filter(Project.country.ilike(f"%{country}%"))
    if verification_level is not None:
        query = query.filter(Project.verification_level >= verification_level)
    if min_score is not None:
        query = query.filter(Project.bankability_score >= min_score)

    # Existing sorting...
    if sort:
        field, direction = sort.rsplit(" ", 1) if " " in sort else (sort, "asc")
        sort_col = getattr(Project, field, None)
        if sort_col:
            query = query.order_by(desc(sort_col) if direction.lower() == "desc" else asc(sort_col))

    # Caching (if using Redis)
    cache_key = f"projects_{sector}_{country}_{verification_level}_{min_score}_{sort}_{page}_{limit}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)  # Indented properly inside the function

    # Pagination
    total = query.count()
    projects = query.offset((page - 1) * limit).limit(limit).all()

    r.set(cache_key, json.dumps([p.__dict__ for p in projects]), ex=300)  # Cache 5 min

    return {
        "projects": projects,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
def calculate_bankability_score(project_data: dict) -> float:
    score = 0.0
    # ... logic from previous (weighted sum for technical, financial, etc.)
    return min(round(score, 1), 10.0)
@app.post("/projects/")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    project_dict = project.dict()
    project_dict["verification_level"] = 0  # V0 on submission
    project_dict["bankability_score"] = calculate_bankability_score(project_dict)
    project_dict["last_verified"] = datetime.utcnow()
class AdminVerification(BaseModel):
    notes: Optional[str] = None
    approved: bool
    verification_level: int
    notes: Optional[str] = None


@app.post("/admin/projects/{project_id}/verify")
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.username == username).first()  # Assume db from Depends(get_db); adjust if needed
    if user is None:
        raise HTTPException(401, "User not found")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(404, "Project not found")

    if verification.verification_level > db_project.verification_level:
        db_project.verification_level = verification.verification_level
        db_project.bankability_score = calculate_bankability_score(db_project.__dict__)
        db_project.last_verified = datetime.utcnow()

    db.commit()
    db.refresh(db_project)
    return db_project

    db.commit()
    db.refresh(db_project)

    # Log the action
    log_action(db, action="verification_approved", user_id=current_admin.id, project_id=project_id,
               details={"new_level": verification.verification_level, "notes": verification.notes})

    return db_project
@app.get("/investors/profile")
def get_investor_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    investor = db.query(Investor).filter(Investor.user_id == current_user.id).first()
    if not investor:
        raise HTTPException(404, "Profile not found")
    return investor

@app.post("/preferences/saved-searches")
def some_function(param1, param2):  # Line 69
    pass  # Add this indented line if empty, or your code here




from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming (e.g., subscribe to alerts; customize as needed)
            await manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.post("/projects/")
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):  # Change to async def
    # ... existing code up to db.commit() ...
    db.commit()
    es.index(index="projects", id=db_project.id, body=db_project.__dict__)
    db.refresh(db_project)

    # Broadcast (await is now allowed)
    await manager.broadcast(f"New project added: {db_project.name} (ID: {db_project.id})")

    return db_project


@app.put("/projects/{project_id}")
async def update_project(project_id: int, project_update: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.dict(exclude_unset=True)
    full_data = {**db_project.__dict__, **update_data}

    update_data["verification_level"] = max(db_project.verification_level, calculate_verification_level(full_data))
    update_data["bankability_score"] = calculate_bankability_score(full_data)
    update_data["last_verified"] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    # Broadcast alert on update
    await manager.broadcast(f"Project {db_project.name} (ID: {project_id}) updated by {current_user.username}")

    return db_project


class Approval(BaseModel):
    approve: bool


@app.post("/intros/{request_id}/approve")
async def approve_intro(request_id: int, approval: Approval, current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    request = db.query(IntroRequest).filter(IntroRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Request not found")

    # Assume sponsor check
    if current_user.role != "sponsor":
        raise HTTPException(403, "Only sponsors can approve")

    request.status = "approved" if approval.approve else "rejected"
    if approval.approve:
        request.approved_at = datetime.utcnow()

    db.commit()

    # Broadcast alert on approval
    if approval.approve:
        await manager.broadcast(
            f"Project ID {request.project_id} approved for intro by sponsor {current_user.username}")

    return {"status": request.status}
@app.post("/projects/{project_id}/admin-review")
def admin_review(project_id: int, review: AdminReview, db: Session = Depends(get_db), current_admin: User = Depends(get_current_user)):
    # Function body starts here with indentation
    pass  # Add this if empty, or your code
@app.post("/intros/{request_id}/approve")
@app.post("/intros/{request_id}/messages")
async def send_message(request_id: int, content: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Indented block starts here with 4 spaces
    request = db.query(IntroRequest).filter(IntroRequest.id == request_id).first()
    if not request or request.status != "approved":
        raise HTTPException(403, "Messaging not enabled")

    message = Message(intro_request_id=request_id, sender_id=current_user.id, content=content)
    db.add(message)
    db.commit()

    # Real-time broadcast (if set up)
    await manager.broadcast(f"New message in intro {request_id}: {content}")

    return {"message_id": message.id}


@app.post("/intros/{request_id}/messages")
async def send_message(request_id: int, content: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Function body starts here with 4 spaces indentation
    request = db.query(IntroRequest).filter(IntroRequest.id == request_id).first()
    if not request or request.status != "approved":
        raise HTTPException(403, "Messaging not enabled")

    message = Message(intro_request_id=request_id, sender_id=current_user.id, content=content)
    db.add(message)
    db.commit()

    # Real-time broadcast
    await manager.broadcast(f"New message in intro {request_id}: {content}")

    return {"message_id": message.id}


@app.get("/admin/pending-v3")
def get_pending_v3(
        sector: Optional[str] = Query(None),
        country: Optional[str] = Query(None),
        min_score: Optional[float] = Query(None),
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_admin)
):
    # Function body
    query = db.query(Project).filter(Project.verification_level == 2)

    if sector:
        query = query.filter(Project.sector.ilike(f"%{sector}%"))
    if country:
        query = query.filter(Project.country.ilike(f"%{country}%"))
    if min_score is not None:
        query = query.filter(Project.bankability_score >= min_score)

    query = query.order_by(desc(Project.bankability_score))

    total = query.count()
    pending = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "pending_projects": pending,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.put("/admin/projects/{project_id}", response_model=Project)
def admin_edit_project(project_id: int, project_update: ProjectCreate, db: Session = Depends(get_db),
                       current_admin: User = Depends(get_current_admin)):
    # Function body starts here with 4 spaces
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.dict(exclude_unset=True)
    full_data = {**db_project.__dict__, **update_data}

    update_data["verification_level"] = max(db_project.verification_level, calculate_verification_level(full_data))
    update_data["bankability_score"] = calculate_bankability_score(full_data)
    update_data["last_verified"] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(db_project, key, value)

    # Log action
    log_action(db, action="project_edited", user_id=current_admin.id, project_id=project_id,
               details={"updated_fields": list(update_data.keys())})

    db.commit()
    db.refresh(db_project)
    return db_project
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        print("Login failed for user", form_data.username)  # Debug
        raise HTTPException(401, "Incorrect credentials")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token}
@app.get("/projects/search")
def search_projects(q: str):
    res = es.search(index="projects", body={"query": {"multi_match": {"query": q, "fields": ["name", "sector", "country"]}}})
    return [hit['_source'] for hit in res['hits']['hits']]