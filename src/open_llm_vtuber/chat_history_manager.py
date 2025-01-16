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

    history_uid = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{str(uuid.uuid4())}"
    conf_dir = _ensure_conf_dir(conf_uid)

    # Create history file with empty metadata
    try:
        filepath = os.path.join(conf_dir, f"{history_uid}.json")
        initial_data = [
            {
                "role": "metadata",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to create new history file: {e}")
        return ""

    logger.debug(f"Created new history file with empty metadata: {filepath}")
    return history_uid


def store_message(
    conf_uid: str, history_uid: str, role: Literal["human", "ai"], content: str
):
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


def get_metadata(conf_uid: str, history_uid: str) -> dict:
    """Get metadata from history file"""
    if not conf_uid or not history_uid:
        return {}

    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        if history_data and history_data[0]["role"] == "metadata":
            return history_data[0]
    except Exception as e:
        logger.error(f"Failed to get metadata: {e}")
    return {}


def update_metadate(conf_uid: str, history_uid: str, metadata: dict) -> bool:
    """Set metadata in history file

    Updates existing metadata with new fields, preserving existing ones.
    If no metadata exists, creates new metadata entry.
    """
    if not conf_uid or not history_uid:
        return False

    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    if not os.path.exists(filepath):
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        if history_data and history_data[0]["role"] == "metadata":
            # Update existing metadata while preserving other fields
            history_data[0].update(metadata)
        else:
            # Create new metadata with timestamp if none exists
            new_metadata = {
                "role": "metadata",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            new_metadata.update(metadata)  # Add new fields
            history_data.insert(0, new_metadata)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Updated metadata for history {history_uid}")
        return True
    except Exception as e:
        logger.error(f"Failed to set metadata: {e}")
    return False


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
            history_data = json.load(f)
            # Filter out metadata
            return [msg for msg in history_data if msg["role"] != "metadata"]
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
            if not filename.endswith(".json"):
                continue

            history_uid = filename[:-5]
            filepath = os.path.join(conf_dir, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    messages = json.load(f)

                    # Filter out metadata for checking if history is empty
                    actual_messages = [
                        msg for msg in messages if msg["role"] != "metadata"
                    ]
                    if not actual_messages:
                        empty_history_uids.append(history_uid)
                        continue

                    latest_message = actual_messages[-1]
                    history_info = {
                        "uid": history_uid,
                        "latest_message": latest_message,
                        "timestamp": latest_message["timestamp"]
                        if latest_message
                        else None,
                    }
                    histories.append(history_info)
            except Exception as e:
                logger.error(f"Error reading history file {filename}: {e}")
                continue

        # Clean up empty histories if there are other non-empty ones
        if len(empty_history_uids) > 0 and len(os.listdir(conf_dir)) > 1:
            for uid in empty_history_uids:
                try:
                    os.remove(os.path.join(conf_dir, f"{uid}.json"))
                    logger.info(f"Removed empty history file: {uid}")
                except Exception as e:
                    logger.error(f"Failed to remove empty history file {uid}: {e}")

        histories.sort(
            key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True
        )
        return histories

    except Exception as e:
        logger.error(f"Error listing histories: {e}")
        return []


def modify_latest_message(
    conf_uid: str,
    history_uid: str,
    role: Literal["human", "ai", "system"],
    new_content: str,
) -> bool:
    """Modify the latest message in a specific history file if it matches the given role"""
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return False

    filepath = os.path.join("chat_history", conf_uid, f"{history_uid}.json")
    if not os.path.exists(filepath):
        logger.warning(f"History file not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        if not history_data:
            logger.warning("History is empty")
            return False

        latest_message = history_data[-1]
        if latest_message["role"] != role:
            logger.warning(
                f"Latest message role ({latest_message['role']}) doesn't match requested role ({role})"
            )
            return False

        latest_message["content"] = new_content
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Successfully modified latest {role} message")
        return True

    except Exception as e:
        logger.error(f"Failed to modify latest message: {e}")
        return False


def rename_history_file(
    conf_uid: str, old_history_uid: str, new_history_uid: str
) -> bool:
    """Rename a history file with a new history_uid"""
    if not conf_uid or not old_history_uid or not new_history_uid:
        logger.warning("Missing required parameters for rename")
        return False

    old_filepath = os.path.join("chat_history", conf_uid, f"{old_history_uid}.json")
    new_filepath = os.path.join("chat_history", conf_uid, f"{new_history_uid}.json")

    try:
        if os.path.exists(old_filepath):
            os.rename(old_filepath, new_filepath)
            logger.info(
                f"Renamed history file from {old_history_uid} to {new_history_uid}"
            )
            return True
    except Exception as e:
        logger.error(f"Failed to rename history file: {e}")
    return False
