from flask import Blueprint, request, jsonify, current_app
from ..utils import parse_inventory_command, get_command_examples
from .db.models import get_db
import json
from datetime import datetime

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    else:
        return obj

@inventory_bp.route("/command", methods=["POST"])
def process_command():
    """
    Process voice/text commands for inventory management.
    
    Expected JSON payload:
    {
        "text": "Add 10 packets of milk"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            current_app.logger.error("No text provided in request")
            return jsonify({
                "success": False,
                "message": "No text provided in request"
            }), 400
        
        text = data["text"].strip()
        
        if not text:
            current_app.logger.error("Empty text provided")
            return jsonify({
                "success": False,
                "message": "Empty text provided"
            }), 400
        
        # Parse the command
        parsed_result = parse_inventory_command(text)
        
        if "error" in parsed_result:
            current_app.logger.error(f"Command parsing error: {parsed_result['error']}")
            return jsonify({
                "success": False,
                "message": parsed_result["error"],
                "command_examples": get_command_examples()
            }), 400
        
        # Execute the command
        action = parsed_result["action"]
        quantity = parsed_result["quantity"]
        product = parsed_result["product"]
        
        db = get_db()
        result = None
        
        if action == "add":
            result = db.add_product(product, quantity)
        elif action == "sell":
            result = db.sell_product(product, quantity)
        elif action == "delete":
            result = db.delete_product(product, quantity)
        else:
            current_app.logger.error(f"Unknown action: {action}")
            return jsonify({
                "success": False,
                "message": f"Unknown action: {action}"
            }), 400
        
        # Serialize the result to handle datetime objects
        serialized_result = serialize_datetime(result)
        
        # Ensure consistent response format
        if serialized_result.get("success"):
            response = {
                "success": True,
                "message": "Text saved successfully!",
                "text": text
            }
            # Add additional data from result if available
            if "action" in serialized_result:
                response["action"] = serialized_result["action"]
            if "product" in serialized_result:
                response["product"] = serialized_result["product"]
            if "quantity" in serialized_result:
                response["quantity"] = serialized_result["quantity"]
            
            current_app.logger.info(f"Command processed successfully: {text}")
            return jsonify(response), 200
        else:
            current_app.logger.error(f"Database operation failed: {serialized_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "message": serialized_result.get("error", "Database operation failed")
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Error processing command: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@inventory_bp.route("/inventory", methods=["GET"])
def get_inventory():
    """
    Get current inventory status.
    
    Returns:
        JSON: List of all products with quantities
    """
    try:
        db = get_db()
        result = db.get_inventory()
        
        # Serialize the result to handle datetime objects
        serialized_result = serialize_datetime(result)
        
        if serialized_result["success"]:
            return jsonify(serialized_result)
        else:
            return jsonify(serialized_result), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting inventory: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500


@inventory_bp.route("/stats", methods=["GET"])
def get_inventory_stats():
    """
    Get inventory statistics for dashboard.
    
    Returns:
        JSON: Inventory statistics including total products, total quantity, etc.
    """
    try:
        db = get_db()
        inventory = db.get_inventory()
        
        # Serialize the inventory to handle datetime objects
        serialized_inventory = serialize_datetime(inventory)
        
        if serialized_inventory["success"]:
            products = serialized_inventory["products"]
            total_products = len(products)
            total_quantity = sum(product["quantity"] for product in products)
            
            # Calculate low stock items (less than 5)
            low_stock_items = [p for p in products if p["quantity"] < 5]
            
            return jsonify({
                "success": True,
                "stats": {
                    "total_products": total_products,
                    "total_quantity": total_quantity,
                    "low_stock_count": len(low_stock_items),
                    "low_stock_items": low_stock_items
                }
            })
        else:
            return jsonify(serialized_inventory), 500
            
    except Exception as e:
        current_app.logger.error(f"Error getting inventory stats: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@inventory_bp.route("/examples", methods=["GET"])
def get_command_examples_route():
    """
    Get examples of valid command formats.
    
    Returns:
        JSON: List of example commands
    """
    try:
        examples = get_command_examples()
        return jsonify({
            "success": True,
            "examples": examples
        })
    except Exception as e:
        current_app.logger.error(f"Error getting command examples: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@inventory_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for inventory service.
    
    Returns:
        JSON: Health status
    """
    try:
        # Get database instance
        db = get_db()
        
        # Check if database is connected
        if hasattr(db, 'client') and db.client and hasattr(db, 'products') and db.products:
            # Test database connection
            db.client.admin.command('ping')
            status = "healthy"
            message = "Inventory service is running and database is connected"
        else:
            # Database not connected
            status = "degraded"
            message = "Inventory service is running but database is not connected"
        
        return jsonify({
            "success": True,
            "status": status,
            "message": message
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }), 500
