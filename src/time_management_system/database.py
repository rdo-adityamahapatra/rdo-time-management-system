"""Database module for MongoDB CRUD operations and connection management."""

import os
import threading
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

from time_management_system.logger import get_logger

logger = get_logger(Path(__file__).stem)


class DBClient:
    """Singleton class for MongoDB CRUD operations.

    Provides thread-safe access to MongoDB with common CRUD operations.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Create or return the singleton instance of DBClient.

        Uses double-checked locking for thread safety.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking for multi-threading safety
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the DBClient, load environment variables, and connect to MongoDB."""
        if self._initialized:
            return

        # Load environment variables from .env file
        load_dotenv()

        self.host = os.getenv("MONGO_HOST")
        self.username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        self.password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        self.database_name = os.getenv("MONGO_INITDB_DATABASE")

        # Handle port conversion with proper error handling
        port_str = os.getenv("MONGO_PORT")
        try:
            self.port = int(port_str) if port_str and port_str.strip() else None
        except ValueError:
            raise OSError(f"Invalid MONGO_PORT value: '{port_str}'. Must be a valid integer.")

        self._validate_env_vars()

        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None

        try:
            self._connect()
        except (ConnectionFailure, PyMongoError) as exc:
            # Reset instance if connection fails
            with self._lock:
                DBClient._instance = None
            logger.error(f"Error during MongoDB connection: {exc}")
            raise

        self._initialized = True

    def _validate_env_vars(self):
        """Validate that all required environment variables are set."""
        required_vars = {
            "MONGO_HOST": self.host,
            "MONGO_PORT": self.port,
            "MONGO_INITDB_ROOT_USERNAME": self.username,
            "MONGO_INITDB_ROOT_PASSWORD": self.password,
            "MONGO_INITDB_DATABASE": self.database_name,
        }

        missing_vars = [var for var, value in required_vars.items() if value is None or value == ""]

        if missing_vars:
            raise OSError(
                f"Missing required environment variables: {', '.join(missing_vars)}. " "Please check your .env file."
            )

    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            # URL-encode username and password to handle special characters
            encoded_username = quote_plus(self.username) if self.username is not None else ""
            encoded_password = quote_plus(self.password) if self.password is not None else ""

            connection_string = f"mongodb://{encoded_username}:{encoded_password}@{self.host}:{self.port}/"
            self._client = MongoClient(connection_string)
            if self.database_name is None:
                raise OSError("Database name must not be None")
            self._database = self._client[self.database_name]

        except ConnectionFailure as exc:
            logger.error(f"Failed to connect to MongoDB: {exc}")
            raise
        except PyMongoError as exc:
            logger.error(f"MongoDB error during connection: {exc}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database."""
        if self._database is None:
            raise RuntimeError("Database connection not established")
        return self._database[collection_name]

    def close_connection(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    # CREATE operations
    def insert_one(self, collection_name: str, document: dict[str, Any]) -> str:
        """Insert a single document into the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as exc:
            logger.error(f"Error inserting document: {exc}")
            raise

    def insert_many(self, collection_name: str, documents: list[dict[str, Any]]) -> list[str]:
        """Insert multiple documents into the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except PyMongoError as exc:
            logger.error(f"Error inserting documents: {exc}")
            raise

    # READ operations
    def find_one(self, collection_name: str, filter_dict: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
        """Find a single document in the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one(filter_dict or {})
            if result and "_id" in result:
                result["_id"] = str(result["_id"])
            return result
        except PyMongoError as exc:
            logger.error(f"Error finding document: {exc}")
            raise

    def find_by_id(self, collection_name: str, document_id: str) -> Optional[dict[str, Any]]:
        """Find a document by its ObjectId."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one({"_id": ObjectId(document_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except InvalidId as exc:
            logger.error(f"Invalid ObjectId format: {exc}")
            raise
        except PyMongoError as exc:
            logger.error(f"Error finding document by ID: {exc}")
            raise

    def find_many(
        self,
        collection_name: str,
        filter_dict: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Find multiple documents in the collection."""
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {})

            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            results = []
            for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            return results
        except PyMongoError as exc:
            logger.error(f"Error finding documents: {exc}")
            raise

    def count_documents(self, collection_name: str, filter_dict: Optional[dict[str, Any]] = None) -> int:
        """Count documents in the collection."""
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {})
        except PyMongoError as exc:
            logger.error(f"Error counting documents: {exc}")
            raise

    # UPDATE operations
    def update_one(
        self, collection_name: str, filter_dict: dict[str, Any], update_dict: dict[str, Any], upsert: bool = False
    ) -> bool:
        """Update a single document in the collection."""
        try:
            collection = self.get_collection(collection_name)

            # Ensure update operations are properly formatted
            if not any(key.startswith("$") for key in update_dict.keys()):
                update_dict = {"$set": update_dict}

            result = collection.update_one(filter_dict, update_dict, upsert=upsert)
            return result.modified_count > 0 or result.upserted_id is not None
        except PyMongoError as exc:
            logger.error(f"Error updating document: {exc}")
            raise

    def update_by_id(self, collection_name: str, document_id: str, update_dict: dict[str, Any]) -> bool:
        """Update a document by its ObjectId."""
        try:
            return self.update_one(collection_name, {"_id": ObjectId(document_id)}, update_dict)
        except InvalidId as exc:
            logger.error(f"Invalid ObjectId format: {exc}")
            raise
        except PyMongoError as exc:
            logger.error(f"Error updating document by ID: {exc}")
            raise

    def update_many(self, collection_name: str, filter_dict: dict[str, Any], update_dict: dict[str, Any]) -> int:
        """Update multiple documents in the collection."""
        try:
            collection = self.get_collection(collection_name)

            # Ensure update operations are properly formatted
            if not any(key.startswith("$") for key in update_dict.keys()):
                update_dict = {"$set": update_dict}

            result = collection.update_many(filter_dict, update_dict)
            return result.modified_count
        except PyMongoError as exc:
            logger.error(f"Error updating documents: {exc}")
            raise

    # DELETE operations
    def delete_one(self, collection_name: str, filter_dict: dict[str, Any]) -> bool:
        """Delete a single document from the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except PyMongoError as exc:
            logger.error(f"Error deleting document: {exc}")
            raise

    def delete_by_id(self, collection_name: str, document_id: str) -> bool:
        """Delete a document by its ObjectId."""
        try:
            return self.delete_one(collection_name, {"_id": ObjectId(document_id)})
        except InvalidId as exc:
            logger.error(f"Invalid ObjectId format: {exc}")
            raise
        except PyMongoError as exc:
            logger.error(f"Error deleting document by ID: {exc}")
            raise

    def delete_many(self, collection_name: str, filter_dict: dict[str, Any]) -> int:
        """Delete multiple documents from the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(filter_dict)
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"Error deleting documents: {exc}")
            raise

    # Utility methods
    def drop_collection(self, collection_name: str) -> bool:
        """Drop an entire collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.drop()
            return True
        except PyMongoError as exc:
            logger.error(f"Error dropping collection: {exc}")
            raise

    def list_collections(self) -> list[str]:
        """List all collections in the database."""
        try:
            if self._database is None:
                raise RuntimeError("Database connection not established")
            return self._database.list_collection_names()
        except PyMongoError as exc:
            logger.error(f"Error listing collections: {exc}")
            raise


# Usage example
if __name__ == "__main__":
    try:
        # Get singleton instance
        db = DBClient()

        # Example CRUD operations
        collection_name = "users"

        # CREATE
        user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}

        user_id = db.insert_one(collection_name, user_data)
        logger.info(f"Inserted user with ID: {user_id}")

        # READ
        user = db.find_by_id(collection_name, user_id)
        logger.info(f"Found user: {user}")

        all_users = db.find_many(collection_name)
        logger.info(f"All users: {len(all_users)} found")

        # UPDATE
        updated = db.update_by_id(collection_name, user_id, {"age": 31})
        logger.info(f"Updated user: {updated}")

        # DELETE
        deleted = db.delete_by_id(collection_name, user_id)
        logger.info(f"Deleted user: {deleted}")

    except OSError as exc:
        logger.error(f"Environment configuration error: {exc}")
    except (ConnectionFailure, PyMongoError) as exc:
        logger.error(f"Database operation failed: {exc}")
    except InvalidId as exc:
        logger.error(f"Invalid ID format: {exc}")

    finally:
        try:
            # Clean up
            db = DBClient()
            db.close_connection()
        except (ConnectionFailure, PyMongoError) as exc:
            logger.error(f"Error closing MongoDB connection: {exc}")
