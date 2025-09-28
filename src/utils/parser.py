import re

def parse_inventory_command(text):
    """
    Parse inventory commands from recognized text.
    
    Supported formats:
    - "Add 10 packets of milk"
    - "Sold 5 soaps"
    - "Delete 2 bottles of oil"
    
    Args:
        text (str): The recognized text from speech
        
    Returns:
        dict: Parsed command with action, quantity, and product
              or error message if format is invalid
    """
    text = text.lower().strip()
    
    # Define patterns for different actions
    patterns = {
        "add": r"add\s+(\d+)\s+(.+)",
        "sell": r"sold\s+(\d+)\s+(.+)",
        "delete": r"delete\s+(\d+)\s+(.+)"
    }
    
    # Try to match each pattern
    for action, pattern in patterns.items():
        match = re.match(pattern, text)
        if match:
            try:
                quantity = int(match.group(1))
                product = match.group(2).strip()
                
                # Validate quantity
                if quantity <= 0:
                    return {"error": "Quantity must be greater than 0"}
                
                return {
                    "action": action,
                    "quantity": quantity,
                    "product": product
                }
            except ValueError:
                return {"error": "Invalid quantity format"}
    
    # If no pattern matches, return error
    return {"error": "Invalid command format. Use: 'Add X [product]', 'Sold X [product]', or 'Delete X [product]'"}

def get_command_examples():
    """
    Return examples of valid command formats for user reference.
    
    Returns:
        list: List of example commands
    """
    return [
        "Add 10 packets of milk",
        "Sold 5 soaps", 
        "Delete 2 bottles of oil",
        "Add 25 apples",
        "Sold 3 bottles of water",
        "Delete 1 chocolate bar"
    ]
