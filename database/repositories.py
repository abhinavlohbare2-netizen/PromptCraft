"""
PromptCraft Database Repositories
---------------------------------
Data access layer for Users, Prompt Evaluations, and History in MongoDB Atlas.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from database.mongodb import get_database


# =========================================================================
# USER REPOSITORY
# =========================================================================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user document by email (case-insensitive)."""
    db = get_database()
    if db is None:
        return None
    try:
        user = db.users.find_one({"email": email.strip().lower()})
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        print(f"[MongoDB] Error fetching user: {e}")
        return None


def create_user(name: str, email: str, password_hash: str, salt: str) -> bool:
    """Inserts a new user document into the users collection."""
    db = get_database()
    if db is None:
        return False

    user_doc = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "salt": salt,
        "created_at": datetime.utcnow()
    }
    try:
        db.users.insert_one(user_doc)
        return True
    except Exception as e:
        print(f"[MongoDB] Error creating user: {e}")
        return False


def update_user_password(email: str, password_hash: str, salt: str) -> bool:
    """Updates password hash and salt for an existing user in MongoDB Atlas."""
    db = get_database()
    if db is None:
        return False
    try:
        res = db.users.update_one(
            {"email": email.strip().lower()},
            {"$set": {
                "password_hash": password_hash,
                "salt": salt,
                "updated_at": datetime.utcnow()
            }}
        )
        return res.modified_count > 0 or res.matched_count > 0
    except Exception as e:
        print(f"[MongoDB] Error updating user password: {e}")
        return False


# =========================================================================
# EVALUATION & OPTIMIZATION REPOSITORY
# =========================================================================

def save_evaluation(
    user_email: str,
    prompt: str,
    eval_result: Dict[str, Any],
    input_type: str = "text"
) -> Optional[str]:
    """
    Saves a prompt evaluation, scores, and complete diagnostic breakdown.
    Returns the string ID of the inserted document.
    """
    db = get_database()
    if db is None:
        return None

    # Extract all 7 parameter scores from parameter_results or scoring breakdown
    param_results = eval_result.get("parameter_results", {})
    scoring_breakdown = eval_result.get("scoring", {}).get("breakdown", {})

    dim_scores = {}
    for p in ["grammar", "readability", "specificity", "context", "completeness", "ambiguity", "constraints"]:
        if p in param_results:
            dim_scores[p] = round(float(param_results[p].get("score", 0.0)), 1)
        elif p in scoring_breakdown:
            dim_scores[p] = round(float(scoring_breakdown[p].get("score", 0.0)), 1)
        elif "scores" in eval_result and p in eval_result["scores"]:
            dim_scores[p] = round(float(eval_result["scores"][p]), 1)
        else:
            dim_scores[p] = 0.0

    tier_info = eval_result.get("quality_tier", {})
    tier_label = tier_info.get("tier", "Needs Work") if isinstance(tier_info, dict) else str(tier_info)

    doc = {
        "user_email": user_email.strip().lower(),
        "input_type": input_type,
        "original_prompt": prompt,
        "overall_score": int(eval_result.get("overall_score", 0)),
        "quality_tier": tier_label,
        "dimension_scores": dim_scores,
        "full_diagnostics": eval_result,
        "created_at": datetime.utcnow()
    }

    try:
        result = db.evaluations.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[MongoDB] Error saving evaluation: {e}")
        return None


def save_optimization(
    eval_id: str,
    user_email: str,
    optimized_prompt: str,
    explanation: str = ""
) -> Optional[str]:
    """Saves the AI-generated improved prompt linked to an evaluation."""
    db = get_database()
    if db is None:
        return None

    doc = {
        "eval_id": eval_id,
        "user_email": user_email.strip().lower(),
        "optimized_prompt": optimized_prompt,
        "explanation": explanation,
        "created_at": datetime.utcnow()
    }

    try:
        result = db.optimizations.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[MongoDB] Error saving optimization: {e}")
        return None


def get_user_evaluations(user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetches user evaluation history, sorted newest first, with all 7 dimension scores."""
    db = get_database()
    if db is None:
        return []

    try:
        cursor = db.evaluations.find(
            {"user_email": user_email.strip().lower()}
        ).sort("created_at", -1).limit(limit)

        evals = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            # Format datetime for easy JSON/UI serialization
            if isinstance(doc.get("created_at"), datetime):
                doc["created_at_formatted"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")

            # Rehydrate dimension_scores across all 7 parameters if missing or zero
            d_scores = doc.get("dimension_scores", {})
            has_valid_scores = any(float(v) > 0 for v in d_scores.values()) if d_scores else False
            
            if not has_valid_scores:
                full_diag = doc.get("full_diagnostics", {})
                param_res = full_diag.get("parameter_results", {}) or full_diag.get("scoring", {}).get("breakdown", {})
                if param_res:
                    doc["dimension_scores"] = {
                        p: round(float(param_res.get(p, {}).get("score", 0.0)), 1)
                        for p in ["grammar", "readability", "specificity", "context", "completeness", "ambiguity", "constraints"]
                    }
                elif doc.get("original_prompt"):
                    from backend.evaluation_engine import evaluate_prompt
                    try:
                        fresh_eval = evaluate_prompt(doc["original_prompt"])
                        doc["dimension_scores"] = {
                            p: round(float(fresh_eval.get("parameter_results", {}).get(p, {}).get("score", 0.0)), 1)
                            for p in ["grammar", "readability", "specificity", "context", "completeness", "ambiguity", "constraints"]
                        }
                    except Exception:
                        pass
            evals.append(doc)
        return evals
    except Exception as e:
        print(f"[MongoDB] Error fetching evaluations: {e}")
        return []


def get_user_statistics(user_email: str) -> Dict[str, Any]:
    """Calculates user stats using MongoDB Aggregation Pipeline."""
    db = get_database()
    if db is None:
        return {"total_prompts": 0, "avg_score": 0, "max_score": 0}

    try:
        pipeline = [
            {"$match": {"user_email": user_email.strip().lower()}},
            {
                "$group": {
                    "_id": None,
                    "total_prompts": {"$sum": 1},
                    "avg_score": {"$avg": "$overall_score"},
                    "max_score": {"$max": "$overall_score"}
                }
            }
        ]

        result = list(db.evaluations.aggregate(pipeline))
        if result:
            res = result[0]
            return {
                "total_prompts": res.get("total_prompts", 0),
                "avg_score": round(res.get("avg_score", 0), 1),
                "max_score": res.get("max_score", 0)
            }
    except Exception as e:
        print(f"[MongoDB] Error calculating statistics: {e}")

    return {"total_prompts": 0, "avg_score": 0, "max_score": 0}


# =========================================================================
# RAG DOCUMENT & EMBEDDING REPOSITORY
# =========================================================================

def save_rag_document(
    user_email: str,
    doc_name: str,
    full_text: str,
    total_chunks: int,
    file_type: str = "pdf",
    file_size_bytes: int = 0
) -> bool:
    """Saves or updates a reference document entry in the rag_documents collection."""
    db = get_database()
    if db is None:
        return False

    doc_entry = {
        "user_email": user_email.strip().lower(),
        "doc_name": doc_name.strip(),
        "file_type": file_type,
        "file_size_bytes": file_size_bytes,
        "total_chunks": total_chunks,
        "word_count": len(full_text.split()),
        "created_at": datetime.utcnow()
    }

    try:
        db.rag_documents.update_one(
            {"user_email": user_email.strip().lower(), "doc_name": doc_name.strip()},
            {"$set": doc_entry},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[MongoDB] Error saving RAG document: {e}")
        return False


def save_rag_chunks(
    user_email: str,
    doc_name: str,
    chunks: List[Dict[str, Any]]
) -> int:
    """
    Saves text chunks and their corresponding Gemini vector embeddings in rag_chunks.
    Replaces any old chunks for this document.
    """
    db = get_database()
    if db is None or not chunks:
        return 0

    u_email = user_email.strip().lower()
    d_name = doc_name.strip()

    try:
        # Remove old chunks for this document
        db.rag_chunks.delete_many({"user_email": u_email, "doc_name": d_name})

        docs_to_insert = []
        for ch in chunks:
            docs_to_insert.append({
                "user_email": u_email,
                "doc_name": d_name,
                "chunk_index": ch["chunk_index"],
                "text": ch["text"],
                "word_count": ch.get("word_count", len(ch["text"].split())),
                "embedding": ch.get("embedding"),  # List of floats (Gemini embedding vector)
                "created_at": datetime.utcnow()
            })

        if docs_to_insert:
            result = db.rag_chunks.insert_many(docs_to_insert)
            return len(result.inserted_ids)
    except Exception as e:
        print(f"[MongoDB] Error saving RAG chunks & embeddings: {e}")

    return 0


def get_user_rag_documents(user_email: str) -> List[Dict[str, Any]]:
    """Retrieves all uploaded reference documents for a user from MongoDB Atlas."""
    db = get_database()
    if db is None:
        return []

    try:
        cursor = db.rag_documents.find(
            {"user_email": user_email.strip().lower()}
        ).sort("created_at", -1)

        docs = []
        for d in cursor:
            d["id"] = str(d.pop("_id"))
            if isinstance(d.get("created_at"), datetime):
                d["created_at_formatted"] = d["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            docs.append(d)
        return docs
    except Exception as e:
        print(f"[MongoDB] Error fetching RAG documents: {e}")
        return []


def get_user_rag_chunks(user_email: str, doc_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves stored chunks and embeddings from MongoDB Atlas for vector similarity search.
    """
    db = get_database()
    if db is None:
        return []

    query: Dict[str, Any] = {"user_email": user_email.strip().lower()}
    if doc_name:
        query["doc_name"] = doc_name.strip()

    try:
        cursor = db.rag_chunks.find(query).sort("chunk_index", 1)
        chunks = []
        for ch in cursor:
            ch["id"] = str(ch.pop("_id"))
            chunks.append(ch)
        return chunks
    except Exception as e:
        print(f"[MongoDB] Error fetching RAG chunks: {e}")
        return []


def delete_rag_document(user_email: str, doc_name: str) -> bool:
    """Deletes a reference document and all its chunks/embeddings from MongoDB Atlas."""
    db = get_database()
    if db is None:
        return False

    u_email = user_email.strip().lower()
    d_name = doc_name.strip()
    try:
        db.rag_documents.delete_one({"user_email": u_email, "doc_name": d_name})
        db.rag_chunks.delete_many({"user_email": u_email, "doc_name": d_name})
        return True
    except Exception as e:
        print(f"[MongoDB] Error deleting RAG document: {e}")
        return False


# =========================================================================
# SAVED PROMPTS REPOSITORY
# =========================================================================

def save_user_saved_prompt(
    user_email: str,
    original_prompt: str,
    optimized_prompt: str,
    overall_score: int = 0,
    key_enhancements: Optional[List[str]] = None
) -> Optional[str]:
    """Saves an optimized prompt to the user's saved prompts collection."""
    db = get_database()
    if db is None:
        return None

    doc = {
        "user_email": user_email.strip().lower(),
        "original_prompt": original_prompt,
        "optimized_prompt": optimized_prompt,
        "overall_score": int(overall_score),
        "key_enhancements": key_enhancements or [],
        "created_at": datetime.utcnow()
    }

    try:
        result = db.saved_prompts.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[MongoDB] Error saving prompt: {e}")
        return None


def get_user_saved_prompts(user_email: str) -> List[Dict[str, Any]]:
    """Retrieves all saved prompts for a user from MongoDB Atlas."""
    db = get_database()
    if db is None:
        return []

    try:
        cursor = db.saved_prompts.find(
            {"user_email": user_email.strip().lower()}
        ).sort("created_at", -1)

        saved = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            if isinstance(doc.get("created_at"), datetime):
                doc["created_at_formatted"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            saved.append(doc)
        return saved
    except Exception as e:
        print(f"[MongoDB] Error fetching saved prompts: {e}")
        return []


def delete_saved_prompt(prompt_id: str, user_email: str) -> bool:
    """Deletes a saved prompt by ID for the specified user."""
    db = get_database()
    if db is None:
        return False

    try:
        from bson import ObjectId
        query: Dict[str, Any] = {"user_email": user_email.strip().lower()}
        try:
            query["_id"] = ObjectId(prompt_id)
        except Exception:
            query["_id"] = prompt_id

        result = db.saved_prompts.delete_one(query)
        return result.deleted_count > 0
    except Exception as e:
        print(f"[MongoDB] Error deleting saved prompt: {e}")
        return False


def toggle_like_saved_prompt(prompt_id: str, user_email: str) -> bool:
    """Toggles the liked / favorite status of a saved prompt."""
    db = get_database()
    if db is None:
        return False

    try:
        from bson import ObjectId
        query: Dict[str, Any] = {"user_email": user_email.strip().lower()}
        try:
            query["_id"] = ObjectId(prompt_id)
        except Exception:
            query["_id"] = prompt_id

        doc = db.saved_prompts.find_one(query)
        if doc:
            current_status = doc.get("is_liked", False)
            new_status = not current_status
            db.saved_prompts.update_one(query, {"$set": {"is_liked": new_status}})
            return new_status
        return False
    except Exception as e:
        print(f"[MongoDB] Error toggling liked prompt: {e}")
        return False



