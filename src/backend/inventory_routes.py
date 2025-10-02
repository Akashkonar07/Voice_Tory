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
        
        # Get user ID from authenticated session
        user_id = getattr(request, 'user', {}).get('user_id')
        
        db = get_db()
        result = None
        
        if action == "add":
            result = db.add_product(product, quantity, user_id=user_id)
        elif action == "sell":
            result = db.sell_product(product, quantity, user_id=user_id)
        elif action == "delete":
            result = db.delete_product(product, quantity, user_id=user_id)
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
        # Get user ID from authenticated session
        user_id = getattr(request, 'user', {}).get('user_id')
        
        db = get_db()
        result = db.get_inventory(user_id=user_id)
        
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
        # Get user ID from authenticated session
        user_id = getattr(request, 'user', {}).get('user_id')
        
        db = get_db()
        inventory = db.get_inventory(user_id=user_id)
        
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

@inventory_bp.route("/delete", methods=["DELETE"])
def delete_inventory_item():
    """
    Delete a product from inventory.
    
    Expected JSON payload:
    {
        "name": "product_name",
        "quantity": 10  (optional, if not provided deletes entire product)
    }
    
    Returns:
        JSON: Delete result with success status and message
    """
    try:
        data = request.get_json()
        
        if not data or "name" not in data:
            return jsonify({
                "success": False,
                "message": "Product name is required"
            }), 400
        
        name = data["name"].strip()
        quantity = data.get("quantity", None)
        
        if not name:
            return jsonify({
                "success": False,
                "message": "Product name cannot be empty"
            }), 400
        
        # Get user ID from authenticated session
        user_id = getattr(request, 'user', {}).get('user_id')
        
        db = get_db()
        
        # If quantity is not provided, delete the entire product
        if quantity is None:
            # Get current inventory to find the product
            inventory = db.get_inventory(user_id=user_id)
            if inventory["success"]:
                product = next((p for p in inventory["products"] if p["name"].lower() == name.lower()), None)
                if product:
                    quantity = product["quantity"]
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Product '{name}' not found"
                    }), 404
        else:
            # Validate quantity
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return jsonify({
                        "success": False,
                        "message": "Quantity must be greater than 0"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "message": "Invalid quantity format"
                }), 400
        
        # Delete the product
        result = db.delete_product(name, quantity, user_id=user_id)
        
        # Serialize the result to handle datetime objects
        serialized_result = serialize_datetime(result)
        
        if serialized_result.get("success"):
            return jsonify({
                "success": True,
                "message": f"Successfully deleted {quantity} units of {name}",
                "product": name,
                "quantity": quantity,
                "action": "deleted"
            })
        else:
            return jsonify({
                "success": False,
                "message": serialized_result.get("error", "Failed to delete product")
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error deleting product: {str(e)}")
        # Ensure we always return JSON, even for unexpected errors
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

@inventory_bp.route("/import-excel", methods=["POST"])
def import_excel():
    """
    Import inventory data from Excel file.
    
    Expected form data:
    - excel_file: Excel file with required columns: name, quantity, cost_price, selling_price
                 Optional columns: total_value, profit (calculated automatically if missing)
    
    Returns:
        JSON: Import result with success status and message
    """
    try:
        if 'excel_file' not in request.files:
            return jsonify({
                "success": False,
                "message": "No Excel file provided"
            }), 400
        
        file = request.files['excel_file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400
        
        # Validate file extension
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                "success": False,
                "message": "Invalid file format. Please upload .xlsx or .xls file"
            }), 400
        
        # Get user ID from authenticated session
        user_id = getattr(request, 'user', {}).get('user_id')
        
        # Process Excel file
        result = process_excel_file(file, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Excel import error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error processing Excel file: {str(e)}"
        }), 500

def process_excel_file(file, user_id=None):
    """
    Process Excel file and import data into inventory.
    
    Args:
        file: Excel file object
        user_id: Optional user ID for user-specific data
        
    Returns:
        dict: Result with success status and message
    """
    try:
        import pandas as pd
        import io
        
        current_app.logger.info(f"Processing Excel file: {file.filename}")
        
        # Read Excel file - handle the uploaded file object properly
        try:
            # Reset file stream position to beginning
            file.stream.seek(0)
            
            # Read the Excel file directly from the file object
            excel_data = pd.read_excel(file.stream)
            current_app.logger.info(f"Excel file read successfully. Shape: {excel_data.shape}")
            current_app.logger.info(f"Columns: {list(excel_data.columns)}")
            current_app.logger.info(f"First few rows: {excel_data.head().to_dict()}")
        except Exception as e:
            current_app.logger.error(f"Error reading Excel file: {str(e)}")
            return {
                "success": False,
                "message": f"Error reading Excel file: {str(e)}"
            }
        
        # Validate required columns (basic required columns)
        required_columns = ['name', 'quantity', 'cost_price', 'selling_price']
        missing_columns = [col for col in required_columns if col not in excel_data.columns]
        
        if missing_columns:
            return {
                "success": False,
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        # Calculate missing optional columns
        if 'total_value' not in excel_data.columns:
            excel_data['total_value'] = excel_data['quantity'] * excel_data['selling_price']
            
        if 'profit' not in excel_data.columns:
            excel_data['profit'] = (excel_data['selling_price'] - excel_data['cost_price']) * excel_data['quantity']
        
        # Clean data - remove rows with missing essential values
        excel_data = excel_data.dropna(subset=['name', 'quantity'])
        
        if len(excel_data) == 0:
            return {
                "success": False,
                "message": "No valid data found in Excel file"
            }
        
        # Get database instance
        db = get_db()
        
        # Get existing inventory for duplicate detection
        existing_inventory = db.get_inventory(user_id)
        if existing_inventory.get('success'):
            existing_products = {item['name'].lower().strip() for item in existing_inventory.get('products', [])}
        else:
            existing_products = set()
        
        # Process each row using to_dict(orient="records") for better data handling
        imported_count = 0
        updated_count = 0
        duplicate_count = 0
        errors = []
        
        # Convert DataFrame to list of dictionaries
        records = excel_data.to_dict(orient="records")
        current_app.logger.info(f"Converted {len(records)} records from Excel")
        
        for index, row_dict in enumerate(records):
            try:
                current_app.logger.info(f"Processing row {index}: {row_dict}")
                
                # Safely extract values with proper type conversion
                name = str(row_dict.get('name', '')).strip()
                quantity_val = row_dict.get('quantity', 0)
                cost_price_val = row_dict.get('cost_price', 0)
                selling_price_val = row_dict.get('selling_price', 0)
                
                # Convert to proper types with error handling
                try:
                    quantity = int(float(quantity_val))
                except (ValueError, TypeError):
                    quantity = 0
                    
                try:
                    cost_price = float(cost_price_val)
                except (ValueError, TypeError):
                    cost_price = 0.0
                    
                try:
                    selling_price = float(selling_price_val)
                except (ValueError, TypeError):
                    selling_price = 0.0
                
                # Calculate total_value and profit if not provided
                try:
                    total_value = float(row_dict.get('total_value', quantity * selling_price))
                except (ValueError, TypeError):
                    total_value = quantity * selling_price
                    
                try:
                    profit = float(row_dict.get('profit', (selling_price - cost_price) * quantity))
                except (ValueError, TypeError):
                    profit = (selling_price - cost_price) * quantity
                
                if not name or quantity <= 0:
                    errors.append(f"Row {index + 2}: Invalid name or quantity")
                    continue
                
                # Validate financial data
                if cost_price < 0 or selling_price < 0 or total_value < 0 or profit < 0:
                    errors.append(f"Row {index + 2}: Financial values cannot be negative")
                    continue
                
                # Validate that selling price is greater than cost price
                if selling_price <= cost_price:
                    errors.append(f"Row {index + 2}: Selling price should be greater than cost price")
                    continue
                
                # Note: total_value and profit validation removed since these are calculated automatically
                # The values are now calculated as: total_value = quantity * selling_price
                # and profit = (selling_price - cost_price) * quantity
                
                # Check for duplicates using normalized name
                normalized_name = normalize_product_name(name)
                
                if normalized_name in existing_products:
                    # Update existing product with financial data
                    current_app.logger.info(f"Updating existing product: {name}")
                    success = db.add_product(
                        name, quantity, 
                        cost_price=cost_price,
                        selling_price=selling_price,
                        total_value=total_value,
                        profit=profit,
                        user_id=user_id
                    )
                    if success:
                        updated_count += 1
                    else:
                        errors.append(f"Row {index + 2}: Failed to update {name}")
                else:
                    # Add new product with financial data
                    current_app.logger.info(f"Adding new product: {name}")
                    success = db.add_product(
                        name, quantity,
                        cost_price=cost_price,
                        selling_price=selling_price,
                        total_value=total_value,
                        profit=profit,
                        user_id=user_id
                    )
                    if success:
                        imported_count += 1
                        existing_products.add(normalized_name)
                    else:
                        errors.append(f"Row {index + 2}: Failed to add {name}")
                        
            except Exception as e:
                current_app.logger.error(f"Error processing row {index + 2}: {str(e)}")
                current_app.logger.error(f"Row data type: {type(row)}")
                current_app.logger.error(f"Row content: {row}")
                errors.append(f"Row {index + 2}: Error processing row - {str(e)}")
        
        # Prepare result message
        message_parts = []
        if imported_count > 0:
            message_parts.append(f"Imported {imported_count} new products")
        if updated_count > 0:
            message_parts.append(f"Updated {updated_count} existing products")
        if duplicate_count > 0:
            message_parts.append(f"Found {duplicate_count} duplicates")
        if errors:
            message_parts.append(f"Encountered {len(errors)} errors")
        
        result_message = ", ".join(message_parts)
        
        return {
            "success": True,
            "message": result_message,
            "imported": imported_count,
            "updated": updated_count,
            "duplicates": duplicate_count,
            "errors": errors
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "pandas library not installed. Please install pandas to use Excel import feature."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing Excel file: {str(e)}"
        }

def normalize_product_name(name):
    """
    Normalize product name for duplicate detection.
    Handles case sensitivity and singular/plural variations.
    
    Args:
        name (str): Product name
        
    Returns:
        str: Normalized product name
    """
    import re
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common plural endings
    plural_endings = ['s', 'es', 'ies', 'ves']
    for ending in plural_endings:
        if normalized.endswith(ending):
            if ending == 'ies':
                normalized = normalized[:-3] + 'y'
            elif ending == 'ves':
                normalized = normalized[:-3] + 'f'
            else:
                normalized = normalized[:-len(ending)]
            break
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized
