from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai

app = FastAPI()

# Load environment variables and configure Genai
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Define the schema for the incoming request
class Query(BaseModel):
    question: str
    data_source: str

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-1.5-pro') # https://ai.google.dev/pricing?authuser=1#1_5pro
    response = model.generate_content([prompt, question])
    return response.text

# Update column and table names for the new dataset
sql_cols_human = 'REQUESTID', 'DATETIMEINIT', 'SOURCE', 'DESCRIPTION', 'REQCATEGORY', 'STATUS', 'REFERREDTO', 'DATETIMECLOSED', 'City', 'State', 'Ward', 'Postcode'
csv_columns_human = ['REQUESTID', 'DATETIMEINIT', 'SOURCE', 'DESCRIPTION', 'REQCATEGORY', 'STATUS', 'REFERREDTO', 'DATETIMECLOSED', 'City', 'State', 'Ward', 'Postcode']
sql_cols = 'REQUESTID', 'DATETIMEINIT', 'SOURCE', 'DESCRIPTION', 'REQCATEGORY', 'STATUS', 'REFERREDTO', 'DATETIMECLOSED', 'City', 'State', 'Ward', 'Postcode'
# csv_columns = ["REQUESTID", "DATETIMEINIT",  "SOURCE", "DESCRIPTION", "REQCATEGORY", "STATUS", "REFERREDTO", "DATETIMECLOSED", "PROBADDRESS" "City", "State", "Ward", "Postcode"]

def get_csv_columns():
    df = pd.read_csv('wandsworth_callcenter_sampled.csv')
    return df.columns.tolist()

csv_columns = get_csv_columns()
print(csv_columns)

sql_prompt = f"""
You are an expert in converting English questions to SQLite code!
The SQLite database has the name CALLCENTER_REQUESTS and has the following Columns: {', '.join(sql_cols)}

Here are some key details about the dataset:
- `SOURCE`: Phone, Online Form, FixMyStreet, Email, Telephone/Email, Telephone Voicemail, Other, Local Council Office.
- `REQCATEGORY`: Blocked Drains, Council Building Maintenance, Fly-Tipping, Street and Pavement Maintenance, Recycling, Traffic Signage Issues, Parks Maintenance, Graffiti Removal, Tree Maintenance.
- `STATUS`: Resolved, In Progress, Cancelled by Customer, Referred to External Agency, Work Order Created, Under Review.
- `REFERREDTO`: Council Enforcement, Transport for London (TfL), Thames Water, Royal Mail, UK Power Networks.

For example:
- Would you please list all unresolved calls? command: SELECT * FROM CALLCENTER_REQUESTS WHERE STATUS='In Progress';
- Would you please count the total number of calls? command: SELECT COUNT(*) FROM CALLCENTER_REQUESTS;
- List all unique wards please? command: SELECT DISTINCT Ward FROM CALLCENTER_REQUESTS;

Also, the SQL code should not have ''' in the beginning or at the end, and SQL word in output.
Ensure that you only generate valid SQLite database queries, not pandas or Python code.
"""



csv_prompt = f"""
You are an expert in analyzing CSV data and converting English questions to pandas query syntax.
The CSV file is named 'wandsworth_callcenter_sampled.csv' and contains residents' call information in Wandsworth Council.
The available columns in the CSV file are: {', '.join(csv_columns)}

Here are some key details about the dataset:
- `SOURCE`: Phone, Online Form, FixMyStreet, Email, Telephone/Email, Telephone Voicemail, Other, Local Council Office.
- `REQCATEGORY`: Blocked Drains, Council Building Maintenance, Fly-Tipping, Street and Pavement Maintenance, Recycling, Traffic Signage Issues, Parks Maintenance, Graffiti Removal, Tree Maintenance.
- `STATUS`: Resolved, In Progress, Cancelled by Customer, Referred to External Agency, Work Order Created, Under Review.
- `REFERREDTO`: Council Enforcement, Transport for London (TfL), Thames Water, Royal Mail, UK Power Networks.

For example:
- How many calls in total? len(df.REQUESTID)
- What are all the calls referred to external agencies? df[df['REFERREDTO'].notna()]
- Would you please show the top 5 most frequent call categories? df['REQCATEGORY'].value_counts().head(5)

Please ensure:
1. Always reference columns using `df['COLUMN_NAME']`.
2. Do not use Python lists like `['COLUMN_NAME']` to refer to columns.
3. Provide only the pandas query syntax without any additional explanation or markdown formatting.
Make sure to use only the columns that are available in the CSV file.
Ensure that you only generate valid pandas queries. NO SQL or other types of code/syntax.

"""

def execute_sql_query(query):
    conn = sqlite3.connect('wandsworth_callcenter_sampled.db')
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        # Capture and explain SQL errors
        sql_error_message = str(e)
        # Send the error message back to Gemini for explanation        
        error_prompt = f"""
        You are an expert SQL debugger and an assistant of the director. An error occurred while executing the following query:
        {query}

        The error was: {sql_error_message}
        Please explain the error in simple laymen terms. Do Not explain. 
        Do Not include any programming code, e.g. sql or python syntax, etc.
        And finally politely remind the user there are only information about the following columns{', '.join(sql_cols_human)}.
        Explain this in layman's terms and remind the user that the dataset contains the following columns: {', '.join(sql_cols_human)}.
        """
        explanation = get_gemini_response("", error_prompt)
        raise HTTPException(status_code=400, detail={"error": sql_error_message, "explanation": explanation})
    finally:
        conn.close()




def execute_pandas_query(query):
    df = pd.read_csv('wandsworth_callcenter_sampled.csv')
    df.columns = df.columns.str.upper()  # Normalize column names to uppercase
    print(f"df is loaded. The first line is: {df.head(1)}")

    # Remove code block indicators (e.g., ```python and ```)
    query = query.replace("```python", "").replace("```", "").strip()

    # Split query into lines
    query_lines = query.split("\n")  # Split into individual statements
    try:
        result = None
        exec_context = {'df': df, 'pd': pd}  # Execution context for exec()
        for line in query_lines:
            line = line.strip()  # Remove extra spaces
            if line:  # Skip empty lines
                print(f"Executing line: {line}")
                exec(line, exec_context)  # Execute each line in the context

        # Retrieve the final result if the last line is a statement
        result = eval(query_lines[-1].strip(), exec_context)  # Evaluate the last line for the result

        print(f"Query Result Before Serialization: {result}")

        # Handle DataFrame results
        if isinstance(result, pd.DataFrame):
            # Replace NaN and infinite values with JSON-compliant values
            result = result.replace([float('inf'), -float('inf')], None).fillna(value="N/A")
            return result.to_dict(orient='records')

        # Handle Series results
        elif isinstance(result, pd.Series):
            result = result.replace([float('inf'), -float('inf')], None).fillna(value="N/A")
            return result.to_dict()

        # Handle scalar results
        else:
            return result

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=f"Pandas Error: {str(e)}")





@app.post("/query")
async def process_query(query: Query):
    if query.data_source == "SQL Database":
        ai_response = get_gemini_response(query.question, sql_prompt)
        try:
            result = execute_sql_query(ai_response)
            return {"query": ai_response, "result": result}
        except HTTPException as e:
            error_detail = e.detail
            return {"query": ai_response, "error": error_detail["error"], "explanation": error_detail["explanation"]}
    else:  # CSV Data
        ai_response = get_gemini_response(query.question, csv_prompt)
        print(f"\n\nai_response: {ai_response}")
        try:
            result = execute_pandas_query(ai_response)
            return {"query": ai_response, "result": result, "columns": csv_columns}
        except HTTPException as e:
            raise HTTPException(status_code=400, detail=f"Error in pandas query: {e.detail}")
