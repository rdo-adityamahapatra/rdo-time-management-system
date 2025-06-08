import os
import threading
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId as BsonInvalidId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, InvalidId, PyMongoError


class DBClient:
    """
    Singleton class for MongoDB CRUD operations.
    Provides thread-safe access to MongoDB with common CRUD operations.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DBClient, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load environment variables from .env file
        load_dotenv()

        # Database configuration - no defaults, must be set in .env
        self.host = os.getenv("MONGO_HOST")
        self.port = int(os.getenv("MONGO_PORT")) if os.getenv("MONGO_PORT") else None
        self.username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        self.password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        self.database_name = os.getenv("MONGO_INITDB_DATABASE")

        # Validate required environment variables
        self._validate_env_vars()

        # Initialize connection
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        self._connect()
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

        missing_vars = [var for var, value in required_vars.items() if value is None]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}. " "Please check your .env file."
            )

    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
            self._client = MongoClient(connection_string)
            self._database = self._client[self.database_name]

            # Test connection
            self._client.admin.command("ping")
            print(f"✅ Connected to MongoDB at {self.host}:{self.port}")

        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
        except PyMongoError as e:
            print(f"❌ MongoDB error during connection: {e}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database."""
        if not self._database:
            raise RuntimeError("Database connection not established")
        return self._database[collection_name]

    def close_connection(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            print("🔌 MongoDB connection closed")

    # CREATE operations
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document into the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"❌ Error inserting document: {e}")
            raise

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents into the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except PyMongoError as e:
            print(f"❌ Error inserting documents: {e}")
            raise

    # READ operations
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find a single document in the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one(filter_dict or {})
            if result and "_id" in result:
                result["_id"] = str(result["_id"])
            return result
        except PyMongoError as e:
            print(f"❌ Error finding document: {e}")
            raise

    def find_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Find a document by its ObjectId."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one({"_id": ObjectId(document_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except (BsonInvalidId, InvalidId) as e:
            print(f"❌ Invalid ObjectId format: {e}")
            raise
        except PyMongoError as e:
            print(f"❌ Error finding document by ID: {e}")
            raise

    def find_many(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
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
        except PyMongoError as e:
            print(f"❌ Error finding documents: {e}")
            raise

    def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in the collection."""
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {})
        except PyMongoError as e:
            print(f"❌ Error counting documents: {e}")
            raise

    # UPDATE operations
    def update_one(
        self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False
    ) -> bool:
        """Update a single document in the collection."""
        try:
            collection = self.get_collection(collection_name)

            # Ensure update operations are properly formatted
            if not any(key.startswith("$") for key in update_dict.keys()):
                update_dict = {"$set": update_dict}

            result = collection.update_one(filter_dict, update_dict, upsert=upsert)
            return result.modified_count > 0 or result.upserted_id is not None
        except PyMongoError as e:
            print(f"❌ Error updating document: {e}")
            raise

    def update_by_id(self, collection_name: str, document_id: str, update_dict: Dict[str, Any]) -> bool:
        """Update a document by its ObjectId."""
        try:
            return self.update_one(collection_name, {"_id": ObjectId(document_id)}, update_dict)
        except (BsonInvalidId, InvalidId) as e:
            print(f"❌ Invalid ObjectId format: {e}")
            raise
        except PyMongoError as e:
            print(f"❌ Error updating document by ID: {e}")
            raise

    def update_many(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """Update multiple documents in the collection."""
        try:
            collection = self.get_collection(collection_name)

            # Ensure update operations are properly formatted
            if not any(key.startswith("$") for key in update_dict.keys()):
                update_dict = {"$set": update_dict}

            result = collection.update_many(filter_dict, update_dict)
            return result.modified_count
        except PyMongoError as e:
            print(f"❌ Error updating documents: {e}")
            raise

    # DELETE operations
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document from the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except PyMongoError as e:
            print(f"❌ Error deleting document: {e}")
            raise

    def delete_by_id(self, collection_name: str, document_id: str) -> bool:
        """Delete a document by its ObjectId."""
        try:
            return self.delete_one(collection_name, {"_id": ObjectId(document_id)})
        except (BsonInvalidId, InvalidId) as e:
            print(f"❌ Invalid ObjectId format: {e}")
            raise
        except PyMongoError as e:
            print(f"❌ Error deleting document by ID: {e}")
            raise

    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents from the collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(filter_dict)
            return result.deleted_count
        except PyMongoError as e:
            print(f"❌ Error deleting documents: {e}")
            raise

    # Utility methods
    def drop_collection(self, collection_name: str) -> bool:
        """Drop an entire collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.drop()
            return True
        except PyMongoError as e:
            print(f"❌ Error dropping collection: {e}")
            raise

    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        try:
            return self._database.list_collection_names()
        except PyMongoError as e:
            print(f"❌ Error listing collections: {e}")
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
        print(f"✅ Inserted user with ID: {user_id}")

        # READ
        user = db.find_by_id(collection_name, user_id)
        print(f"📖 Found user: {user}")

        all_users = db.find_many(collection_name)
        print(f"📚 All users: {len(all_users)} found")

        # UPDATE
        updated = db.update_by_id(collection_name, user_id, {"age": 31})
        print(f"✏️ Updated user: {updated}")

        # DELETE
        deleted = db.delete_by_id(collection_name, user_id)
        print(f"🗑️ Deleted user: {deleted}")

    except EnvironmentError as exc:
        print(f"❌ Environment configuration error: {exc}")
    except (ConnectionFailure, PyMongoError) as exc:
        print(f"❌ Database operation failed: {exc}")
    except (BsonInvalidId, InvalidId) as exc:
        print(f"❌ Invalid ID format: {exc}")

    finally:
        try:
            # Clean up
            db = DBClient()
            db.close_connection()
        except:
            pass
