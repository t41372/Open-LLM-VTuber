import os
import json
import uuid
from datetime import datetime
from typing import Literal, List, TypedDict
from loguru import logger

class HistoryMessage(TypedDict):
    role: Literal["human", "ai"]
    timestamp: str
    content: str

def _ensure_conf_dir(conf_uid: str) -> str:
    """Ensure the directory for a specific conf exists and return its path"""
    base_dir = os.path.join("chat_history", conf_uid)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def create_new_history(conf_uid: str) -> str:
    """Create a new history file with a unique ID and return the history_uid"""
    if not conf_uid:
        logger.warning("No conf_uid provided")
        return ""
    
    history_uid = str(uuid.uuid4())
    conf_dir = _ensure_conf_dir(conf_uid)
    
    # Create empty history file
    filepath = os.path.join(conf_dir, f"{history_uid}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([], f)
    
    logger.debug(f"Created new history file: {filepath}")
    return history_uid

def store_message(conf_uid: str, history_uid: str, role: Literal["human", "ai"], content: str):
    """Store a message in a specific history file"""
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return
    
    conf_dir = _ensure_conf_dir(conf_uid)
    filepath = os.path.join(conf_dir, f"{history_uid}.json")
    logger.debug(f"Storing {role} message to {filepath}")
    
    history_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception:
            pass
    
    now_str = datetime.now().isoformat(timespec="seconds")
    new_item = {
        "role": role,
        "timestamp": now_str,
        "content": content,
    }
    history_data.append(new_item)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    logger.debug(f"Successfully stored {role} message")

def get_history_uids(conf_uid: str) -> List[str]:
    """Get all history UIDs for a specific conf"""
    if not conf_uid:
        return []
    
    conf_dir = _ensure_conf_dir(conf_uid)
    try:
        # List all .json files and remove the .json extension
        return [f[:-5] for f in os.listdir(conf_dir) if f.endswith('.json')]
    except Exception:
        return []

def get_history(conf_uid: str, history_uid: str) -> List[HistoryMessage]:
    """Read chat history for the given conf_uid and history_uid"""
    if not conf_uid or not history_uid:
        return []
    
    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def delete_history(conf_uid: str, history_uid: str) -> bool:
    """Delete a specific history file"""
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return False
    
    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Successfully deleted history file: {filepath}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete history file: {e}")
    return False 