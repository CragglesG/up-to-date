"""Utility functions for the Up To Date Slack bot."""

from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException


class EnumUpdateFailed(Exception):
    """Raised when an update fails."""


def clean_string(string: str) -> str:
    """Clean a string to be used as a document ID."""
    cleaned = (
        string.replace(" ", "-")
        .replace("?", "_")
        .replace("!", "_")
        .replace(":", "_")
        .replace(";", "_")
        .replace(",", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace("+", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("|", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace("[", "_")
        .replace("]", "_")
        .replace("{", "_")
        .replace("}", "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace('"', "_")
        .replace("'", "_")
        .replace("`", "_")
        .replace("~", "_")
        .replace("@", "_")
        .replace("#", "_")
        .replace("$", "_")
        .replace("%", "_")
        .replace("^", "_")
        .replace("*", "_")
        .replace("¦", "_")
        .replace("¬", "_")
        .replace("£", "_")
        .replace("€", "_")
        .replace("¥", "_")
        .replace("₹", "_")
        .replace("§", "_")
        .replace("©", "_")
        .replace("®", "_")
        .replace("™", "_")
        .replace("°", "_")
        .replace("±", "_")
    )
    return cleaned


def add_or_update_user(db_instance: Databases, document_id: str, data: dict) -> None:
    """Try to update the user document in the database.
    If the document does not exist, create it."""
    try:
        db_instance.update_document(
            "topics-and-channels", "ts-and-cs-data", document_id, data
        )
    except AppwriteException:
        db_instance.create_document(
            "topics-and-channels", "ts-and-cs-data", document_id, data
        )


def add_or_update_post(db_instance: Databases, document_id: str, data: dict) -> None:
    """Try to update the post document in the database.
    If the document does not exist, create it."""
    try:
        db_instance.update_document("utd-posts", "posts-data", document_id, data)
    except AppwriteException:
        db_instance.create_document("utd-posts", "posts-data", document_id, data)


def get_topics(db_instance: Databases) -> dict:
    """Get all topics from the database."""
    documents = db_instance.list_documents("topics-and-channels", "all-topics")[
        "documents"
    ]
    topics = {
        "topic-names": [doc["topic-name"] for doc in documents],
        "topic-ids": [doc["topic-id"] for doc in documents],
    }
    return topics
