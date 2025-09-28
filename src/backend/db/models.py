from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

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
        if "name" in query:
            name = query["name"]
            for doc_id, doc in self.storage.items():
                if doc.get("name") == name:
                    return doc
        return None
    
    def update_one(self, query, update):
        """Update one document matching the query."""
        if "name" in query:
            name = query["name"]
            for doc_id, doc in self.storage.items():
                if doc.get("name") == name:
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
    
    def find(self, query=None):
        """Find all documents."""
        results = list(self.storage.values())
        return type('Cursor', (), (), {'__iter__': lambda self: iter(results)})(results)

class InventoryDatabase:
    def __init__(self):
        """Initialize database connection for inventory management."""
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db = None
        self.products = None
        self.sales = None
        self.client = None
        self.in_memory_storage = {}
        
        # If in development mode, use in-memory storage
        if DEV_MODE:
            print("🔧 Development mode: Using in-memory storage")
            self.products = InMemoryCollection(self.in_memory_storage)
            self.sales = InMemoryCollection({})
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
            
            # Test connection and create index
            self.client.admin.command('ping')
            self.products.create_index([("name", 1)], unique=True)
            
            print("✅ Connected to MongoDB")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("💡 Falling back to in-memory storage")
            self.products = InMemoryCollection(self.in_memory_storage)
            self.sales = InMemoryCollection({})
    
    def add_product(self, name, quantity):
        """
        Add products to inventory or update existing product quantity.
        """
        try:
            existing = self.products.find_one({"name": name})
            
            if existing:
                # Update existing product
                self.products.update_one(
                    {"name": name}, 
                    {"$inc": {"quantity": quantity}}
                )
                action = "updated"
            else:
                # Insert new product
                self.products.insert_one({
                    "name": name, 
                    "quantity": quantity,
                    "created_at": datetime.now()
                })
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
    
    def sell_product(self, name, quantity):
        """
        Sell products from inventory (reduce quantity).
        """
        try:
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
            self.products.update_one(
                {"name": name}, 
                {"$inc": {"quantity": -quantity}}
            )
            
            # Record the sale
            self.sales.insert_one({
                "name": name,
                "quantity": quantity,
                "timestamp": datetime.now()
            })
            
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
    
    def delete_product(self, name, quantity):
        """
        Delete products from inventory (reduce quantity).
        """
        try:
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
    
    def get_inventory(self):
        """
        Get all products in inventory.
        """
        try:
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
        
    def add_product(self, name, quantity):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def sell_product(self, name, quantity):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def delete_product(self, name, quantity):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration."
        }
    
    def get_inventory(self):
        return {
            "success": False,
            "error": "Database connection failed. Please check your MongoDB configuration.",
            "products": []
        }
