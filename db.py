import streamlit as st
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
import mysql.connector
import os
from altair.vegalite.v4.api import Chart
import altair as alt


# Function to save the question and answer to a text file
def save_response(question, answer):
    with open("responses.txt", "a") as file:
        file.write(f"Question: {question}\n")
        file.write(f"Answer: {answer}\n")
        file.write("\n")


def clear_responses():
    with open("responses.txt", "w") as file:
        file.write("")


# Establish a connection to the database
def fetch_data_from_database():
    print("Fetching data from the database...")
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Vellore@21',
        database='bank'
    )

    cursor = connection.cursor()
    tables = ['customer', 'branch', 'account', 'trandetails', 'loan']

    for table in tables:
        # Check if 'summarized' column exists in the table
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'summarized';")
        result = cursor.fetchone()

        if result is None:
            # Add 'summarized' column to the table
            query = f"ALTER TABLE {table} ADD COLUMN summarized VARCHAR(255);"
            cursor.execute(query)
            connection.commit()

        # Get the columns of the table
        cursor.execute(f"DESCRIBE {table};")
        columns = [column[0] for column in cursor.fetchall()]
        print(f"\n\nColumns: {columns} \n")

        # Remove 'summarized' column from the list
        columns.remove('summarized')

        # # Update the 'summarized' column
        # query2 = f"UPDATE {table} SET summarized = CONCAT("
        # for i in range(len(columns)):
        #     query2 += f"""; {columns[i]}: ", TRIM({columns[i]}),\n"""
        #
        # query2 += "; )"
        #
        # cursor.execute(query2)
        # connection.commit()

        # Update the 'summarized' column
        query2 = f"UPDATE {table} SET summarized = CONCAT_WS(', ', "
        for i in range(len(columns)):
            query2 += f"CONCAT('{columns[i]}: ', TRIM({columns[i]})), "

        query2 = query2[:-2]  # Remove the last ', ' separator
        query2 += ")"

        cursor.execute(query2)
        connection.commit()

    # Fetch the 'summarized' data from each table
    extracted_data = {}
    for table in tables:
        cursor.execute(f"SELECT summarized FROM {table}")
        rows = cursor.fetchall()
        extracted_data[table] = rows

    cursor.close()
    connection.close()

    return extracted_data


def main():
    st.title("Database Question Answering")

    datas = fetch_data_from_database()
    print(datas)
    data_split = CharacterTextSplitter(
        separator=", ",
        chunk_size=1000,
        chunk_overlap=300,
        length_function=len,
    )
    datas = ", ".join(str(data) for data in datas)  # Convert integers to strings before joining

    datas = data_split.split_text(datas)
    print(datas)

    import os
    import openai
    os.environ["OPENAI_API_KEY"] = "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"
    openai.api_key = "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"

    embeddings = OpenAIEmbeddings(openai_api_key= "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")
    docsearch = FAISS.from_texts(datas, embeddings)

    chain = load_qa_chain(OpenAI(), chain_type="stuff")

    query = st.text_input("Enter your question:")
    if st.button("Get Answer"):
        response = docsearch.similarity_search(query)
        answer = chain.run(input_documents=response, question=query)
        st.write(f"Answer: {answer}")
        save_response(query, answer)

    with open("responses.txt", "r") as file:
        previous_responses = file.read().splitlines()

    if st.button("Clear Responses"):
        clear_responses()
        st.write("All previous responses cleared.")

    # Display previous responses
    st.subheader("Previous Responses")
    for i, response in enumerate(previous_responses):

        if response.startswith("Question:"):
            st.write(f"Question: {response[10:]}")
        elif response.startswith("Answer:"):
            st.write(f"Answer: {response[8:]}")
        else:
            st.write("")


if __name__ == '__main__':
    main()
