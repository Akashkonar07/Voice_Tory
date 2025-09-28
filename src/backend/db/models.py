from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import hashlib
import secrets
import re

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default configuration")

# Check if we're in development mode
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'

class InMemoryCollection:
    """In-memory collection that mimics MongoDB collection behavior."""
    
    def __init__(self, storage_dict):
        self.storage = storage_dict
        self.counter = 0
    
    def find_one(self, query):
        """Find one document matching the query."""
        for doc_id, doc in self.storage.items():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                return doc
        return None
    
    def update_one(self, query, update):
        """Update one document matching the query."""
        for doc_id, doc in self.storage.items():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                if "$inc" in update:
                    for field, value in update["$inc"].items():
                        doc[field] = doc.get(field, 0) + value
                return True
        return False
    
    def insert_one(self, document):
        """Insert a new document."""
        self.counter += 1
        doc_id = str(self.counter)
        document["_id"] = doc_id
        self.storage[doc_id] = document
        return type('InsertResult', (), {'inserted_id': doc_id})()
    
    def delete_one(self, query):
        """Delete one document matching the query."""
        for doc_id, doc in list(self.storage.items()):
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                del self.storage[doc_id]
                return True
        return False
    
    def find(self, query=None):
        """Find all documents."""
        if query is None:
            results = list(self.storage.values())
        else:
            results = []
            for doc_id, doc in self.storage.items():
                match = True
                for key, value in query.items():
                    if doc.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(doc)
        return type('Cursor', (), (), {'__iter__': lambda self: iter(results)})(results)

class InventoryDatabase:
    def __init__(self):
        """Initialize database connection for inventory management."""
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db = None
        self.products = None
        self.sales = None
        self.users = None
        self.sessions = None
        self.client = None
        self.in_memory_storage = {}
        self.in_memory_users = {}
        self.in_memory_sessions = {}
        
        # If in development mode, use in-memory storage
        if DEV_MODE:
            print("🔧 Development mode: Using in-memory storage")
            self.products = InMemoryCollection(self.in_memory_storage)
            self.sales = InMemoryCollection({})
            self.users = InMemoryCollection(self.in_memory_users)
            self.sessions = InMemoryCollection(self.in_memory_sessions)
            return
        
        try:
            # MongoDB connection
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True,
                w='majority',
                appName='VoiceTory'
            )
            self.db = self.client['inventory_management']
            self.products = self.db['products']
            self.sales = self.db['sales']
            self.users = self.db['users']
            self.sessions = self.db['sessions']
            
            # Test connection and create indexes
            self.client.admin.command('ping')
            self.products.create_index([("name", 1)], unique=True)
            self.users.create_index([("email", 1)], unique=True)
            self.users.create_index([("username", 1)], unique=True)
            self.sessions.create_index([("session_token", 1)], unique=True)
            self.sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)
            
            print("✅ Connected to MongoDB")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("💡 Falling back to in-memory storage")
            self.products = InMemoryCollection(self.in_memory_storage)
            self.sales = InMemoryCollection({})
            self.users = InMemoryCollection(self.in_memory_users)
            self.sessions = InMemoryCollection(self.in_memory_sessions)
    
    def add_product(self, name, quantity, user_id=None):
        """
        Add products to inventory or update existing product quantity.
        """
        try:
            # If user_id is provided, check for existing product for that user
            if user_id:
                existing = self.products.find_one({"name": name, "user_id": user_id})
            else:
                existing = self.products.find_one({"name": name})
            
            if existing:
                # Update existing product
                if user_id:
                    self.products.update_one(
                        {"name": name, "user_id": user_id}, 
                        {"$inc": {"quantity": quantity}}
                    )
                else:
                    self.products.update_one(
                        {"name": name}, 
                        {"$inc": {"quantity": quantity}}
                    )
                action = "updated"
            else:
                # Insert new product
                product_data = {
                    "name": name, 
                    "quantity": quantity,
                    "created_at": datetime.now()
                }
                if user_id:
                    product_data["user_id"] = user_id
                
                self.products.insert_one(product_data)
                action = "added"
            
            return {
                "success": True,
                "action": action,
                "product": name,
                "quantity": quantity
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sell_product(self, name, quantity, user_id=None):
        """
        Sell products from inventory (reduce quantity).
        """
        try:
            # If user_id is provided, find product for that specific user
            if user_id:
                item = self.products.find_one({"name": name, "user_id": user_id})
            else:
                item = self.products.find_one({"name": name})
            
            if not item:
                return {
                    "success": False,
                    "error": "Product not found"
                }
            
            if item["quantity"] < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient stock. Available: {item['quantity']}"
                }
            
            # Update product quantity
            if user_id:
                self.products.update_one(
                    {"name": name, "user_id": user_id}, 
                    {"$inc": {"quantity": -quantity}}
                )
            else:
                self.products.update_one(
                    {"name": name}, 
                    {"$inc": {"quantity": -quantity}}
                )
            
            # Record the sale
            sale_data = {
                "name": name,
                "quantity": quantity,
                "timestamp": datetime.now()
            }
            if user_id:
                sale_data["user_id"] = user_id
            
            self.sales.insert_one(sale_data)
            
            return {
                "success": True,
                "action": "sold",
                "product": name,
                "quantity": quantity
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_product(self, name, quantity, user_id=None):
        """
        Delete products from inventory (reduce quantity).
        """
        try:
            # If user_id is provided, find product for that specific user
            if user_id:
                item = self.products.find_one({"name": name, "user_id": user_id})
            else:
                item = self.products.find_one({"name": name})
            
            if not item:
                return {
                    "success": False,
                    "error": "Product not found"
                }
            
            if item["quantity"] < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient quantity. Available: {item['quantity']}"
                }
            
            # Update product quantity
            if user_id:
                self.products.update_one(
                    {"name": name, "user_id": user_id}, 
                    {"$inc": {"quantity": -quantity}}
                )
                
                # Remove product if quantity becomes 0
                updated_item = self.products.find_one({"name": name, "user_id": user_id})
                if updated_item and updated_item["quantity"] == 0:
                    self.products.delete_one({"name": name, "user_id": user_id})
            else:
                self.products.update_one(
                    {"name": name}, 
                    {"$inc": {"quantity": -quantity}}
                )
                
                # Remove product if quantity becomes 0
                updated_item = self.products.find_one({"name": name})
                if updated_item and updated_item["quantity"] == 0:
                    self.products.delete_one({"name": name})
            
            return {
                "success": True,
                "action": "deleted",
                "product": name,
                "quantity": quantity
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_inventory(self, user_id=None):
        """
        Get all products in inventory for a specific user or all products.
        """
        try:
            if user_id:
                # Get products for specific user
                products = list(self.products.find({"user_id": user_id}, {"_id": 0}))
            else:
                # Get all products (backward compatibility)
                products = list(self.products.find({}, {"_id": 0}))
            
            return {
                "success": True,
                "products": products
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # User Authentication Methods
    def create_user(self, username, email, password, full_name=None):
        """
        Create a new user account.
        """
        try:
            # Validate input
            if not username or not email or not password:
                return {
                    "success": False,
                    "error": "Username, email, and password are required"
                }
            
            # Validate email format
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                return {
                    "success": False,
                    "error": "Invalid email format"
                }
            
            # Check if user already exists
            existing_user = self.users.find_one({"$or": [{"username": username}, {"email": email}]})
            if existing_user:
                return {
                    "success": False,
                    "error": "Username or email already exists"
                }
            
            # Hash password
            salt = secrets.token_hex(16)
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            
            # Create user
            user_data = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "salt": salt,
                "full_name": full_name or username,
                "created_at": datetime.now(),
                "is_active": True,
                "role": "user"
            }
            
            result = self.users.insert_one(user_data)
            
            return {
                "success": True,
                "user_id": result.inserted_id,
                "username": username,
                "email": email
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def authenticate_user(self, username, password):
        """
        Authenticate user with username/email and password.
        """
        try:
            # Find user by username or email
            user = self.users.find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            if not user.get("is_active", True):
                return {
                    "success": False,
                    "error": "Account is deactivated"
                }
            
            # Verify password
            password_hash = hashlib.sha256((password + user["salt"]).encode()).hexdigest()
            if password_hash != user["password_hash"]:
                return {
                    "success": False,
                    "error": "Invalid password"
                }
            
            return {
                "success": True,
                "user_id": user["_id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user.get("role", "user")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_session(self, user_id, username):
        """
        Create a new session for authenticated user.
        """
        try:
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)  # 24 hour expiry
            
            session_data = {
                "session_token": session_token,
                "user_id": user_id,
                "username": username,
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "is_active": True
            }
            
            result = self.sessions.insert_one(session_data)
            
            return {
                "success": True,
                "session_token": session_token,
                "expires_at": expires_at
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_session(self, session_token):
        """
        Validate session token and return user info.
        """
        try:
            session = self.sessions.find_one({"session_token": session_token})
            
            if not session:
                return {
                    "success": False,
                    "error": "Invalid session token"
                }
            
            if not session.get("is_active", True):
                return {
                    "success": False,
                    "error": "Session is inactive"
                }
            
            if session["expires_at"] < datetime.now():
                return {
                    "success": False,
                    "error": "Session has expired"
                }
            
            return {
                "success": True,
                "user_id": session["user_id"],
                "username": session["username"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_session(self, session_token):
        """
        Delete session (logout).
        """
        try:
            result = self.sessions.delete_one({"session_token": session_token})
            
            if result.deleted_count > 0:
                return {
                    "success": True,
                    "message": "Session deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global database instance (lazy initialization)
db = None

def get_db():
    """Get database instance with lazy initialization."""
    global db
    if db is None:
        try:
            db = InventoryDatabase()
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            # Return a mock database that returns error responses
            return MockDatabase()
    return db

class MockDatabase:
    """Mock database for when MongoDB connection fails."""
    
    def __init__(self):
        self.client = None
        self.products = None
        
    def add_product(self, name, quantity, user_id=None):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def sell_product(self, name, quantity, user_id=None):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def delete_product(self, name, quantity, user_id=None):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def get_inventory(self, user_id=None):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration.",
            "products": []
        }
    
    def create_user(self, username, email, password, full_name=None):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def authenticate_user(self, username, password):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def create_session(self, user_id, username):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def validate_session(self, session_token):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def delete_session(self, session_token):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
