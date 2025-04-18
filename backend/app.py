# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from dotenv import load_dotenv
import traceback
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Helper function to validate environment variables
def validate_env_vars():
    required_vars = ["OPENROUTER_API_KEY", "GOOGLE_SHEET_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

# Configure OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# Configure Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
gc = None
sheet = None
expenses_worksheet = None

def init_google_sheets():
    """Initialize the connection to Google Sheets"""
    global gc, sheet, expenses_worksheet
    
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
        gc = gspread.authorize(credentials)
        
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        logger.info(f"Attempting to open sheet with ID: {sheet_id}")
        
        sheet = gc.open_by_key(sheet_id)
        worksheets = sheet.worksheets()
        logger.info(f"Available worksheets: {[ws.title for ws in worksheets]}")
        
        # Check if Expenses worksheet exists, create it if not
        try:
            expenses_worksheet = sheet.worksheet("Expenses")
            logger.info("Found 'Expenses' worksheet")
        except gspread.exceptions.WorksheetNotFound:
            logger.info("'Expenses' worksheet not found, creating it...")
            expenses_worksheet = sheet.add_worksheet(title="Expenses", rows=1000, cols=4)
            # Add header row
            expenses_worksheet.append_row(["Date", "Category", "Amount", "Description"])
            logger.info("Created 'Expenses' worksheet with headers")
        
        return True
    except FileNotFoundError:
        logger.error("credentials.json file not found")
        return False
    except Exception as e:
        logger.error(f"Error connecting to Google Sheets: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Helper functions
def make_ai_request(messages):
    try:
        response = requests.post(OPENROUTER_URL, headers=OPENROUTER_HEADERS, json={
            "model": "google/gemini-2.0-flash-001",
            "messages": messages,
            "temperature": 0.1
        })

        if response.status_code != 200:
            logger.error(f"AI API Error: {response.status_code} - {response.text}")
            return "I'm having trouble understanding that right now. Can you try rephrasing?"

        json_response = response.json()

        if "choices" not in json_response or not json_response["choices"]:
            logger.warning("AI returned an empty response.")
            return "I couldn't process that request. Could you provide more details?"

        return json_response["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while connecting to AI: {str(e)}")
        return "I had trouble connecting to my AI service. Please try again."

    except Exception as e:
        logger.error(f"Unexpected AI error: {str(e)}")
        return "Something went wrong on my end. Can you try again?"

def parse_formatting_request(query):
    """Use AI to extract formatting details from natural language"""
    try:
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant designed to extract Google Sheets formatting instructions from user messages.
                              Identify and extract the following fields:
                              - format_type: The type of formatting (e.g., font, color, background, alignment, bold, italic)
                              - value: The value to apply (e.g., "red", "Arial", "12", "center", "true")
                              - target: What to apply formatting to (e.g., "A1:B5", "column A", "row 3", "header row", "Expenses column")
                              - sheet_name: Optional name of the sheet to format (default to "Expenses")
                              
                              For colors, return standard color names or hex codes.
                              For font sizes, return numeric values.
                              For ranges, try to convert natural language to A1 notation when possible.
                              
                              Ensure your response is in valid JSON format and contains only the relevant fields—no additional text or explanations."""
            },
            {"role": "user", "content": query}
        ]
        
        content = make_ai_request(messages)
        if not content:
            logger.error("Failed to get response from AI for formatting extraction")
            return None
        
        # Try to extract JSON from response
        try:
            # Clean the response to ensure it's valid JSON
            content = content.strip()
            # Remove any markdown code block markers if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            
            # Validate the required fields
            if 'format_type' not in data or not data['format_type']:
                logger.warning("No format type extracted from query")
                return None
                
            if 'value' not in data or not data['value']:
                logger.warning("No format value extracted from query")
                return None
                
            if 'target' not in data or not data['target']:
                logger.warning("No target range extracted from query")
                return None
                
            if 'sheet_name' not in data:
                data['sheet_name'] = "Expenses"
                
            logger.info(f"Extracted formatting details: {data}")
            return data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from AI: {content}")
            return None
    except Exception as e:
        logger.error(f"Error extracting formatting details: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def convert_target_to_a1_notation(target, worksheet=None):
    """Convert natural language target to A1 notation"""
    try:
        # If target is already in A1 notation, return it
        if re.match(r'^[A-Z]+[0-9]+:[A-Z]+[0-9]+$', target) or re.match(r'^[A-Z]+[0-9]+$', target):
            return target
            
        # If worksheet is provided, we can use it to get actual dimensions
        if worksheet:
            all_values = worksheet.get_all_values()
            num_rows = len(all_values)
            num_cols = len(all_values[0]) if all_values else 0
        else:
            # Default to some reasonable values
            num_rows = 1000
            num_cols = 26
            
        # Convert column name references
        target_lower = target.lower()
        
        # Headers row
        if "header" in target_lower or "headers" in target_lower:
            return "A1:Z1"
            
        # Handle specific column references
        if "column" in target_lower:
            # Try to extract column letter
            col_match = re.search(r'column\s+([a-zA-Z])', target_lower)
            if col_match:
                col_letter = col_match.group(1).upper()
                return f"{col_letter}1:{col_letter}{num_rows}"
                
            # Try to extract column name from our known columns
            known_columns = {
                "date": "A", 
                "category": "B", 
                "amount": "C", 
                "description": "D"
            }
            
            for col_name, col_letter in known_columns.items():
                if col_name.lower() in target_lower:
                    return f"{col_letter}1:{col_letter}{num_rows}"
        
        # Handle specific row references
        if "row" in target_lower:
            row_match = re.search(r'row\s+(\d+)', target_lower)
            if row_match:
                row_num = row_match.group(1)
                return f"A{row_num}:Z{row_num}"
                
        # Handle "all cells" or "entire sheet"
        if "all" in target_lower or "entire" in target_lower or "everything" in target_lower:
            return f"A1:Z{num_rows}"
            
        # Default to header row if we couldn't parse
        logger.warning(f"Could not parse target '{target}', defaulting to header row")
        return "A1:Z1"
            
    except Exception as e:
        logger.error(f"Error converting target to A1 notation: {str(e)}")
        logger.error(traceback.format_exc())
        return "A1:Z1"  # Default to header row
app.route('/format_sheet', methods=['POST'])
def format_sheet():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized"}), 500
        
    try:
        data = request.json
        logger.info(f"Received format_sheet request: {data}")
        
        if 'text' not in data:
            return jsonify({"status": "Error", "message": "Missing 'text' field in request"}), 400
            
        # Extract formatting details from the text
        format_data = parse_formatting_request(data['text'])
        if not format_data:
            return jsonify({
                "status": "Error", 
                "message": "Couldn't extract formatting details. Please be more specific about what formatting you want to apply."
            }), 400
            
        # Get the worksheet
        sheet_name = format_data.get('sheet_name', 'Expenses')
        try:
            target_worksheet = sheet.worksheet(sheet_name)
            logger.info(f"Found worksheet: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet not found: {sheet_name}")
            return jsonify({"status": "Error", "message": f"Worksheet '{sheet_name}' not found"}), 404
            
        # Apply the formatting
        if apply_formatting(format_data, target_worksheet):
            return jsonify({
                "status": "Success",
                "message": f"Applied {format_data['format_type']} formatting to {format_data['target']}",
                "data": format_data
            })
        else:
            return jsonify({
                "status": "Error",
                "message": "Failed to apply formatting changes"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in format_sheet: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/update_expense', methods=['POST'])
def update_expense():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized"}), 500

    try:
        data = request.json
        row_number = data.get("row_number")  # Row number to update (1-based index)
        if not row_number or row_number < 2:
            return jsonify({"status": "Error", "message": "Invalid row number"}), 400

        # Fetch the current expenses
        all_expenses = expenses_worksheet.get_all_records()
        if row_number > len(all_expenses) + 1:
            return jsonify({"status": "Error", "message": "Row number out of range"}), 400

        # Extract new values (keep old ones if not provided)
        old_expense = all_expenses[row_number - 2]  # Adjusting for zero-based index
        updated_expense = {
            "Date": data.get("date", old_expense["Date"]),
            "Category": data.get("category", old_expense["Category"]),
            "Amount": data.get("amount", old_expense["Amount"]),
            "Description": data.get("description", old_expense["Description"]),
        }

        # Update the row in the Google Sheet
        expenses_worksheet.update(f"A{row_number}:D{row_number}", [[
            updated_expense["Date"],
            updated_expense["Category"],
            updated_expense["Amount"],
            updated_expense["Description"]
        ]])

        return jsonify({"status": "Success", "message": "Expense updated!", "updated_expense": updated_expense})

    except Exception as e:
        logger.error(f"Error in update_expense: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "Error", "message": str(e)}), 500



def apply_formatting(format_data, worksheet=None):
    """Apply formatting to Google Sheets based on extracted format data"""
    try:
        if not worksheet:
            logger.error("Worksheet not provided for formatting")
            return False
            
        format_type = format_data.get('format_type', '').lower()
        value = format_data.get('value', '')
        target = format_data.get('target', '')
        
        # Convert target to A1 notation
        range_notation = convert_target_to_a1_notation(target, worksheet)
        logger.info(f"Converted target '{target}' to range '{range_notation}'")
        
        # Create format request based on format type
        if format_type in ['font', 'font size', 'fontsize', 'size']:
            try:
                size = int(value)
                worksheet.format(range_notation, {
                    "fontSize": size
                })
                logger.info(f"Applied font size {size} to range {range_notation}")
            except ValueError:
                logger.error(f"Invalid font size value: {value}")
                return False
                
        elif format_type in ['color', 'font color', 'fontcolor', 'text color', 'textcolor']:
            worksheet.format(range_notation, {
                "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
            })
            
            if value.lower() == 'red':
                worksheet.format(range_notation, {
                    "textFormat": {"foregroundColor": {"red": 1, "green": 0, "blue": 0}}
                })
            elif value.lower() == 'green':
                worksheet.format(range_notation, {
                    "textFormat": {"foregroundColor": {"red": 0, "green": 0.8, "blue": 0}}
                })
            elif value.lower() == 'blue':
                worksheet.format(range_notation, {
                    "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 1}}
                })
            elif value.lower() == 'black':
                worksheet.format(range_notation, {
                    "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
                })
            # Add more color options as needed
            
            logger.info(f"Applied text color {value} to range {range_notation}")
                
        elif format_type in ['background', 'background color', 'backgroundcolor']:
            worksheet.format(range_notation, {
                "backgroundColor": {"red": 1, "green": 1, "blue": 1}  # Default white
            })
            
            if value.lower() == 'red':
                worksheet.format(range_notation, {
                    "backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}
                })
            elif value.lower() == 'green':
                worksheet.format(range_notation, {
                    "backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}
                })
            elif value.lower() == 'blue':
                worksheet.format(range_notation, {
                    "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 1}
                })
            elif value.lower() == 'yellow':
                worksheet.format(range_notation, {
                    "backgroundColor": {"red": 1, "green": 1, "blue": 0.8}
                })
            elif value.lower() == 'gray' or value.lower() == 'grey':
                worksheet.format(range_notation, {
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
            # Add more color options as needed
            
            logger.info(f"Applied background color {value} to range {range_notation}")
                
        elif format_type in ['bold']:
            is_bold = value.lower() in ['true', 'yes', 'y', '1', 'on']
            worksheet.format(range_notation, {
                "textFormat": {"bold": is_bold}
            })
            logger.info(f"Applied bold={is_bold} to range {range_notation}")
                
        elif format_type in ['italic']:
            is_italic = value.lower() in ['true', 'yes', 'y', '1', 'on']
            worksheet.format(range_notation, {
                "textFormat": {"italic": is_italic}
            })
            logger.info(f"Applied italic={is_italic} to range {range_notation}")
                
        elif format_type in ['alignment', 'align']:
            if value.lower() in ['center', 'centre']:
                worksheet.format(range_notation, {
                    "horizontalAlignment": "CENTER"
                })
            elif value.lower() in ['left']:
                worksheet.format(range_notation, {
                    "horizontalAlignment": "LEFT"
                })
            elif value.lower() in ['right']:
                worksheet.format(range_notation, {
                    "horizontalAlignment": "RIGHT"
                })
            logger.info(f"Applied alignment={value} to range {range_notation}")
                
        else:
            logger.warning(f"Unsupported format type: {format_type}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error applying formatting: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def extract_expense_details(query):
    """Use AI to extract expense details from natural language, supporting multiple expenses."""
    try:
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant designed to extract and manage expense details from user messages accurately. 
                              Identify and extract the following fields for each expense:
                              - category: The type of expense (e.g., food, travel, rent).
                              - amount: A numeric value representing the expense amount (exclude currency symbols).
                              - date: The date of the expense in YYYY-MM-DD format (leave empty if not specified).
                              - description: A brief summary of the expense based on the provided message.

                              If multiple expenses are mentioned, return a LIST of objects, each containing these fields.
                              Ensure your response is in valid JSON format and contains only the relevant fields—no additional text or explanations."""
            },
            {"role": "user", "content": query}
        ]

        content = make_ai_request(messages)
        if not content:
            logger.error("Failed to get response from AI for expense extraction")
            return None

        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            
            if isinstance(data, list):  # Handle multiple expenses
                parsed_expenses = []
                for expense in data:
                    parsed_expenses.append(validate_expense_data(expense))
                return parsed_expenses
            elif isinstance(data, dict):  # Handle single expense
                return [validate_expense_data(data)]
            else:
                logger.error("Unexpected response format from AI")
                return None
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from AI: {content}")
            return None
        except ValueError as e:
            logger.error(f"Value error parsing amount: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error extracting expense details: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def validate_expense_data(data):
    """Ensures all required fields are present and properly formatted."""
    if 'category' not in data or not data['category']:
        data['category'] = 'Uncategorized'
    
    if 'amount' not in data or not data['amount']:
        logger.warning("No amount extracted from query")
        data['amount'] = 0
    
    if isinstance(data['amount'], str):
        cleaned_amount = data['amount'].replace('$', '').replace('£', '').replace('€', '').replace(',', '')
        try:
            data['amount'] = float(cleaned_amount)
        except ValueError:
            data['amount'] = 0
            logger.error("Failed to convert amount to float")
    
    if 'date' not in data or not data['date']:
        data['date'] = datetime.now().strftime('%Y-%m-%d')
    
    if 'description' not in data:
        data['description'] = ''
    
    return data


def get_expense_summary():
    """Generate a summary of expenses"""
    try:
        # Get all expense data from sheet
        data = expenses_worksheet.get_all_records()
        
        if not data:
            logger.info("No expense data found")
            return {
                "total_spent": 0,
                "top_category": None,
                "category_breakdown": {}
            }
        
        # Total spent
        total_spent = sum(float(record['Amount']) for record in data)
        
        # Spending by category
        categories = {}
        for record in data:
            category = record['Category']
            try:
                amount = float(record['Amount'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid amount value in record: {record}")
                amount = 0
                
            if category in categories:
                categories[category] += amount
            else:
                categories[category] = amount
        
        # Find top category
        top_category = max(categories.items(), key=lambda x: x[1]) if categories else (None, 0)
        
        logger.info(f"Generated expense summary: Total={total_spent}, Top category={top_category[0]}")
        return {
            "total_spent": total_spent,
            "top_category": top_category[0],
            "top_category_amount": top_category[1],
            "category_breakdown": categories
        }
    except Exception as e:
        logger.error(f"Error generating expense summary: {str(e)}")
        logger.error(traceback.format_exc())
        return None

# Routes
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized"}), 500
        
    try:
        data = request.json
        logger.info(f"Received add_expense request: {data}")
        
        # If raw text is provided, extract expense details
        if 'text' in data:
            extracted_data = extract_expense_details(data['text'])
            if not extracted_data:
                return jsonify({"status": "Error", "message": "Failed to extract expense details"}), 400
            
            category = extracted_data.get('category', 'Uncategorized')
            amount = extracted_data.get('amount', 0)
            date = extracted_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            description = extracted_data.get('description', '')
        else:
            # Otherwise use provided structured data
            category = data.get('category', 'Uncategorized')
            amount = data.get('amount', 0)
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
            description = data.get('description', '')
        
        # Add to Google Sheet
        logger.info(f"Adding expense: {date}, {category}, {amount}, {description}")
        expenses_worksheet.append_row([date, category, amount, description])
        
        return jsonify({
            "status": "Success", 
            "message": "Expense added!",
            "expense": {
                "category": category,
                "amount": amount,
                "date": date,
                "description": description
            }
        })
    except Exception as e:
        logger.error(f"Error in add_expense: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/get_expenses', methods=['GET'])
def get_expenses():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized"}), 500
        
    try:
        category = request.args.get('category', None)
        logger.info(f"Getting expenses, category filter: {category}")
        
        # Get all expense data from sheet
        data = expenses_worksheet.get_all_records()
        
        # Filter by category if specified
        if category and category != 'All':
            data = [record for record in data if record['Category'].lower() == category.lower()]
        
        logger.info(f"Found {len(data)} expenses")
        return jsonify({
            "status": "Success",
            "expenses": data
        })
    except Exception as e:
        logger.error(f"Error in get_expenses: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "Error", "message": str(e)}), 500

def get_recent_expenses():
    """Fetches the last N expenses from the Google Sheet"""
    try:
        all_expenses = expenses_worksheet.get_all_records()

        if not all_expenses:
            return {"status": "Error", "message": "No expenses found."}

        recent_expenses = all_expenses[-5:]  # Fetch last 5 expenses
        
        return {"status": "Success", "expenses": recent_expenses}

    except Exception as e:
        logger.error(f"Error retrieving recent expenses: {str(e)}")
        return {"status": "Error", "message": "Failed to retrieve recent expenses."}


@app.route('/expense_summary', methods=['GET'])
def expense_summary():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized"}), 500
        
    try:
        logger.info("Generating expense summary")
        summary = get_expense_summary()
        if not summary:
            return jsonify({"status": "Error", "message": "Failed to generate expense summary"}), 500
        
        return jsonify({
            "status": "Success",
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error in expense_summary: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "Error", "message": str(e)}), 500

def generate_ai_response(intent, context):
    """Generates a natural AI-based response for different intents."""
    messages = [
    {
        "role": "system",
        "content": f"""You are an intelligent and helpful AI assistant for an expense tracker app. 
                       Your goal is to generate clear, natural, and engaging responses based on the given intent and context. 
                       
                       - Ensure responses are **conversational, user-friendly, and informative**.
                       - If an action is successfully completed, **confirm the outcome in a positive and concise manner**.
                       - If clarification is needed, **ask follow-up questions to guide the user**.
                       - If the requested action isn't possible, **suggest alternative solutions**.
                       
                       **Example Behaviors:**
                       - For updates or deletions, confirm the exact changes.
                       - For insights, provide a brief summary followed by details.
                       - For errors, provide actionable next steps.

                       Always maintain a polite, professional, and engaging tone."""
    },
    {
        "role": "user",
        "content": f"""User has requested an action in the expense tracker.
                       
                       **Intent:** {intent}  
                       **Context:** {json.dumps(context, indent=2)}  

                       Generate the best possible response based on the provided details."""
    }
]
    return make_ai_request(messages)



@app.route('/process_query', methods=['POST'])
def process_query():
    if not expenses_worksheet:
        return jsonify({"status": "Error", "message": "Google Sheets connection not initialized. Please check your settings."}), 500

    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({"status": "Error", "message": "I didn't receive a valid query. Please try again."}), 400

        query = data.get('query', '').strip()
        logger.info(f"Processing query: {query}")

        if not query:
            return jsonify({"status": "Error", "message": "I received an empty query. Can you provide more details?"}), 400

        intent_messages = [
    {
        "role": "system",
        "content": """You are an AI assistant for an expense tracker app. 
                      Analyze the user's request and strictly match it to one of the following intents:

                      - add_expense
                      - delete_expense
                      - update_expense
                      - get_total_expense
                      - get_highest_spending
                      - get_recent_expenses
                      - get_expense_summary
                      - format_sheet
                      - greet
                      - help

                      If the query does not match any of these, return 'unknown'. 
                      Do NOT create new intents. Always select from the given list."""
    },
    {"role": "user", "content": query}
]

        intent = make_ai_request(intent_messages)
        if not intent or intent.lower() == "unknown":
            return jsonify({"status": "Error", "message": "I'm not sure how to handle that request. Can you try asking differently?"}), 400

        intent = intent.strip().lower()
        logger.info(f"Detected intent: {intent}")

        if intent == "add_expense":
            extracted_data = extract_expense_details(query)

            if not extracted_data:
                return jsonify({"status": "Error", "message": "Failed to extract expense details."}), 400

            for expense in extracted_data:
                expenses_worksheet.append_row([
                    expense.get("date", datetime.now().strftime('%Y-%m-%d')),
                    expense.get("category", "Uncategorized"),
                    expense.get("amount", 0),
                    expense.get("description", "")
                ])

            response_text = generate_ai_response("add_expense", {"count": len(extracted_data), "expenses": extracted_data})
            return jsonify({"status": "Success", "message": response_text})

        elif intent == "delete_expense":
            logger.info("Processing delete_expense intent")

    # Extract row number first
            row_number_message = [{"role": "system", "content": "Extract the row number if present. Return 'None' if not found."}, {"role": "user", "content": query}]
            row_number_response = make_ai_request(row_number_message)

            try:
                row_number = int(row_number_response.strip())
            except ValueError:
                row_number = None

            if row_number:
                logger.info(f"Deleting expense at row {row_number}")
                expenses_worksheet.delete_rows(row_number)
                response_text = generate_ai_response("delete_expense", {"row_number": row_number})
                return jsonify({"status": "Success", "message": response_text})

            # Extract category name for deletion
            category_message = [
    {"role": "system", "content": "Extract ONLY the exact category name from the query. Return just the category name, nothing else."},
    {"role": "user", "content": query}
]
            category = make_ai_request(category_message).strip()


            logger.info(f"Extracted category: {category}")  # Debugging log

            if category:
                all_expenses = expenses_worksheet.get_all_records()

                # Normalize category (handle empty cells & trim spaces)
                matching_rows = [
                    idx + 2 for idx, exp in enumerate(all_expenses) 
                    if exp.get("Category", "").strip().lower() == category.lower()
                ]

                if not matching_rows:
                    logger.warning(f"No expenses found for category: {category}")
                    return jsonify({"status": "Error", "message": f"No expenses found for category: {category}"}), 400

                # Delete rows from bottom to top (prevents index shifting)
                for row in reversed(matching_rows):
                    expenses_worksheet.delete_rows(row)

                response_text = generate_ai_response("delete_expense", {"category": category, "count": len(matching_rows)})
                return jsonify({"status": "Success", "message": response_text})

            return jsonify({"status": "Error", "message": "Could not extract row number or category for deletion."}), 400

        elif intent == "update_expense":
            update_details = extract_expense_details(query)
            if not update_details:
                return jsonify({"status": "Error", "message": "Couldn't extract update details."}), 400

            row_number_message = [{"role": "system", "content": "Extract the row number if present."}, {"role": "user", "content": query}]
            row_number_response = make_ai_request(row_number_message)
            try:
                row_number = int(row_number_response.strip())
            except ValueError:
                row_number = None

            if row_number:
                expenses_worksheet.update(f"A{row_number}:D{row_number}", [[
                    update_details.get("date", datetime.now().strftime('%Y-%m-%d')),
                    update_details.get("category", "Uncategorized"),
                    update_details.get("amount", 0),
                    update_details.get("description", "")
                ]])
                response_text = generate_ai_response("update_expense", {"row_number": row_number, "new_data": update_details})
                return jsonify({"status": "Success", "message": response_text})

        elif intent in ["get_total_expense", "get_highest_spending", "get_recent_expenses", "get_expense_summary", "format_sheet"]:
            response_function = globals().get(intent)

            if response_function is None or not callable(response_function):
                logger.error(f"Function {intent} is not defined or callable.")
                return jsonify({"status": "Error", "message": f"Sorry, the '{intent}' function is not available."}), 500

            logger.info(f"Calling function: {intent}")  # Debug log

            try:
                response = response_function()

                if not response or not isinstance(response, dict):
                    logger.error(f"Unexpected response format from {intent}: {response}")
                    return jsonify({"status": "Error", "message": "Unexpected response format from function."}), 500

                response_text = generate_ai_response(intent, response)
                return jsonify({"status": "Success", "message": response_text})

            except Exception as e:
                logger.error(f"Error executing function {intent}: {str(e)}")
                return jsonify({"status": "Error", "message": f"Failed to execute '{intent}': {str(e)}"}), 500


        elif intent == "greet":
            response_text = generate_ai_response("greet", {})
            return jsonify({"status": "Success", "message": response_text})
        
        elif intent == "types of help that user wants":
            response_text = generate_ai_response("help", {})
            return jsonify({"status": "Success", "message": response_text})

        else:
            return jsonify({"status": "Error", "message": "Unknown intent"}), 400
    except Exception as e:
        logger.error(f"Error in process_query: {str(e)}")
        return jsonify({"status": "Error", "message": f"Internal Server Error: {str(e)}"}), 500





@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint to check if the service is running and connections are working"""
    status = {
        "api": "running",
        "google_sheets": expenses_worksheet is not None,
        "openrouter": OPENROUTER_API_KEY is not None
    }
    
    if all(status.values()):
        return jsonify({"status": "healthy", "details": status})
    else:
        return jsonify({"status": "unhealthy", "details": status}), 503

@app.before_first_request
def before_first_request():
    """Initialize connections before the first request"""
    if not validate_env_vars():
        logger.error("Required environment variables are missing. Service may not function correctly.")
    
    if not init_google_sheets():
        logger.error("Failed to initialize Google Sheets connection")

if __name__ == '__main__':
    # Initialize connections at startup
    validate_env_vars()
    init_google_sheets()
    
    app.run(debug=True)