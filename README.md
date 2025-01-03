# CallDataAI - Wandsworth Council Call Center Analysis

**CallDataAI** is an AI-powered application designed to analyze Wandsworth Council's call center data. It enables users to interact with the data using natural language queries, generating SQL or Pandas queries, and providing actionable insights.

## Features
- **Natural Language Queries**: Input queries in plain English.
- **SQL and Pandas Support**: Automatically generates SQL queries for databases and Pandas queries for CSV datasets.
- **Interactive Dashboard**: Streamlit-powered user interface for seamless interaction.
- **FastAPI Backend**: Backend API for processing and responding to user queries.

## How to Run Locally
1. **Clone the repository**:
   ```bash
   git clone https://github.com/entzyeung/calldataai.git
   cd calldataai
   ```

2. **Set up dependencies**:
   - Create a virtual environment and install dependencies:
     ```bash
     python -m venv venv
     source venv/bin/activate  # For Windows: venv\Scripts\activate
     pip install -r requirements.txt
     ```

3. **Set up environment variables**:
   - Create a `.env` file in the project root and add your Google API key:
     ```plaintext
     GOOGLE_API_KEY=your_real_api_key
     ```

4. **Run the backend**:
   ```bash
   uvicorn backend:app --reload
   ```

5. **Run the frontend**:
   ```bash
   streamlit run frontend.py
   ```

6. Open your browser and navigate to:
   - **Frontend**: [http://localhost:7860](http://localhost:7860)
   - **Backend**: [http://localhost:8000](http://localhost:8000)

## How to Deploy
### Using Docker
1. **Build the Docker image**:
   ```bash
   docker build -t calldataai-app .
   ```

2. **Run the Docker container**:
   ```bash
   docker run -p 8000:8000 -p 7860:7860 calldataai-app
   ```

3. Access the app at [http://localhost:7860](http://localhost:7860).

### Using Hugging Face Spaces
- Follow the deployment instructions for Hugging Face Spaces.
- Add your `GOOGLE_API_KEY` in the secrets manager.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
