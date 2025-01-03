import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="CallDataAI - Wandsworth Council NetCall Analysis",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("📞 CallDataAI")
st.sidebar.markdown(
    """
    **Welcome to CallDataAI**, your AI-powered assistant for analyzing Wandsworth Council's NetCall data. Use the menu below to:
    - Select the data source (SQL/CSV)
    - Run pre-defined or custom queries
    - Gain actionable insights
    """
)

st.sidebar.markdown("### Select Data Source:")
data_source = st.sidebar.radio("", ('SQL Database', 'CSV Database'))

st.sidebar.markdown("### Common Queries:")
common_queries = {
    'SQL Database': [
        'List all unique Source',
        'List all unique request categories',
        'List all unique wards and their postcodes',
        'Count the total number of calls',
        'List all unresolved calls',
        'What are the total number of requests per year?',
        'What are the average time (days) to close request per request category?',
    ],
    'CSV Database': [
        'Count total number of call requests',
        'List all calls referred to external agencies',
        'Show top 5 most frequent call categories',
    ]
}

for idx, query in enumerate(common_queries[data_source]):
    if st.sidebar.button(query, key=f"query_button_{idx}"):
        st.session_state["common_query"] = query

st.title("📞 CallDataAI - Wandsworth Council NetCall Analysis")
st.markdown(
    """
    **CallDataAI** is an AI-powered chatbot designed for analyzing Wandsworth Council's NetCall data.
    Input natural language queries to explore the data and gain actionable insights.
    """
)

with st.container():
    st.markdown("### Enter Your Question")
    question = st.text_input(
        "Input:", key="input", value=st.session_state.get("common_query", ""), placeholder="Type your query here..."
    )
    submit = st.button("Submit", type="primary")

if submit:
    with st.spinner("Processing your request..."):
        response = requests.post(
            "http://localhost:8000/query", json={"question": question, "data_source": data_source}
        )

    if response.status_code == 200:
        data = response.json()

        if "error" in data:
            with st.expander("Error Explanation"):
                st.error(data["explanation"])

        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### Generated {'SQL' if data_source == 'SQL Database' else 'Pandas'} Query")
                st.code(data["query"], language="sql" if data_source == "SQL Database" else "python")

            with col2:
                st.markdown("### Query Results")
                result = data["result"]

                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        df = pd.DataFrame(result)
                        st.dataframe(df)
                    elif isinstance(result[0], list):
                        df = pd.DataFrame(result)
                        st.dataframe(df)
                    else:
                        st.write(result)

                elif isinstance(result, dict):
                    st.json(result)

                else:
                    st.write(result)

            if data_source == "CSV Database":
                st.markdown("### Available CSV Columns")
                st.write(data["columns"])

            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []

            st.session_state["chat_history"].append(f"🔧({data_source}): {question}")
            st.session_state["chat_history"].append(f"🤖: {data['query']}")

    else:
        st.error(f"Error processing your request: {response.text}")

with st.container():
    st.markdown("### Chat History")
    if "chat_history" in st.session_state:
        for message in st.session_state["chat_history"]:
            st.text(message)
    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        st.success("Chat history cleared!")

st.markdown("---")
st.markdown("Developed by Lorentz Yeung, 2024 Christmas")
st.markdown("Contact: lorentzyeung@gmail.com or lorentz.yeung@richmondandwandsworth.gov.uk")
