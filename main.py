import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timezone

from database import db, create_document, get_documents
from schemas import User, Post, Comment

app = FastAPI(title="Hashnode-like Blog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ObjectIdStr(BaseModel):
    id: str


def validate_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "Blog API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Routes: Users
@app.post("/api/users", response_model=dict)
def create_user(user: User):
    # Enforce unique username/email
    if db["user"].find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    if db["user"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    inserted_id = create_document("user", user)
    return {"id": inserted_id}


@app.get("/api/users", response_model=List[dict])
def list_users():
    users = get_documents("user")
    for u in users:
        u["id"] = str(u.pop("_id"))
    return users


# Routes: Posts
class CreatePost(Post):
    pass


@app.post("/api/posts", response_model=dict)
def create_post(post: CreatePost):
    # Ensure author exists
    if not db["user"].find_one({"username": post.author_username}):
        raise HTTPException(status_code=404, detail="Author not found")
    inserted_id = create_document("post", post)
    return {"id": inserted_id}


@app.get("/api/posts", response_model=List[dict])
def list_posts(tag: Optional[str] = None, author: Optional[str] = None):
    query = {}
    if tag:
        query["tags"] = tag
    if author:
        query["author_username"] = author
    posts = get_documents("post", query)
    for p in posts:
        p["id"] = str(p.pop("_id"))
    # sort newest first by created_at if present
    posts.sort(key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return posts


@app.get("/api/posts/{post_id}", response_model=dict)
def get_post(post_id: str):
    oid = validate_object_id(post_id)
    doc = db["post"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


# Routes: Comments
class CreateComment(Comment):
    pass


@app.post("/api/posts/{post_id}/comments", response_model=dict)
def add_comment(post_id: str, comment: CreateComment):
    # Ensure author exists
    if not db["user"].find_one({"username": comment.author_username}):
        raise HTTPException(status_code=404, detail="Comment author not found")
    oid = validate_object_id(post_id)
    payload = {
        "author_username": comment.author_username,
        "content": comment.content,
        "created_at": datetime.now(timezone.utc),
    }
    result = db["post"].update_one({"_id": oid}, {"$push": {"comments": payload}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True}


# Health
@app.get("/api/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
