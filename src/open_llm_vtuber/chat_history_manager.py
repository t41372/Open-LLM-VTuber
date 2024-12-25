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
    try:
        filepath = os.path.join(conf_dir, f"{history_uid}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        logger.error(f"Failed to create new history file: {e}")
        return ""
    
    logger.debug(f"Created new history file: {filepath}")
    return history_uid

def store_message(conf_uid: str, history_uid: str, role: Literal["human", "ai"], content: str):
    """Store a message in a specific history file"""
    if not conf_uid or not history_uid:
        if not conf_uid:
            logger.warning("Missing conf_uid")
        if not history_uid:
            logger.warning("Missing history_uid")
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
            logger.error(f"Failed to load history file: {filepath}")
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

def get_history(conf_uid: str, history_uid: str) -> List[HistoryMessage]:
    """Read chat history for the given conf_uid and history_uid"""
    if not conf_uid or not history_uid:
        if not conf_uid:
            logger.warning("Missing conf_uid")
        if not history_uid:
            logger.warning("Missing history_uid")
        return []
    
    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    
    if not os.path.exists(filepath):
        logger.warning(f"History file not found: {filepath}")
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

def get_history_list(conf_uid: str) -> List[dict]:
    """Get list of histories with their latest messages"""
    if not conf_uid:
        return []
    
    histories = []
    conf_dir = _ensure_conf_dir(conf_uid)
    empty_history_uids = []  
    
    try:
        for filename in os.listdir(conf_dir):
            if not filename.endswith('.json'):
                continue
                
            history_uid = filename[:-5]
            filepath = os.path.join(conf_dir, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    messages = json.load(f)
                    if not messages:  
                        empty_history_uids.append(history_uid)
                        continue
                        
                    latest_message = messages[-1]
                    history_info = {
                        "uid": history_uid,
                        "latest_message": latest_message,
                        "timestamp": latest_message["timestamp"] if latest_message else None
                    }
                    histories.append(history_info)
            except Exception as e:
                logger.error(f"Error reading history file {filename}: {e}")
                continue
        
        if len(empty_history_uids) > 0 and len(os.listdir(conf_dir)) > 1:
            for uid in empty_history_uids:
                try:
                    os.remove(os.path.join(conf_dir, f"{uid}.json"))
                    logger.info(f"Removed empty history file: {uid}")
                except Exception as e:
                    logger.error(f"Failed to remove empty history file {uid}: {e}")
                
        histories.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True)
        return histories
        
    except Exception as e:
        logger.error(f"Error listing histories: {e}")
        return []
