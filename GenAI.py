import streamlit as st
import pandas as pd
from google import genai
import plotly.express as px
import os

#main confi page
st.set_page_config(page_title="oneClick Dashboard", layout="wide")
st.title("oneClick Dashboard")

#text input for API key and type password 
api_key =st.sidebar.text_input("Enter your Google GenAI API Key", type="password")

if not api_key:
    st.warning("Please enter your Google GenAI API Key to continue.")
    st.stop()

client = genai.Client(api_key=api_key)

uploaded_file =st.file_uploader("Upload your CSV file", type=["csv"])   

if uploaded_file is not None:
    df =pd.read_csv(uploaded_file)
    coloum =list(df.columns)
    st.success("File uploaded successfully!")
    st.write("Columns in the dataset:", coloum)
    st.dataframe(df.head(4))

    #colum names and import name must menctioned in the prompt
    prompt = f"""
    You are an expert Python data analyst. I have a pandas DataFrame named 'df'
    with the following columns: {', '.join(coloum)}.
    Write Python code using the library `plotly.express` as `px` to create a meaningful chart from this data.
    Assign the resulting plotly figure to a variable named `fig`.
   
    Return ONLY the raw python code. Do not include markdown formatting like ```python.
    Do not explain the code. Just the code.
    """
    if st.button("Generate Dashboard"):
        #spinner loading display
        with st.spinner("AI is writing the dashboard code..."):
            try:
              # call llm 
              response = client.models.generate_content(
                  model="gemini-3.5-flash",
                    contents=prompt
              )
              generated_code = response.text.strip()
              #when ai create markdown format code so use this remove that
              if generated_code.startswith("```python"):
                    generated_code = generated_code[9:-3].strip()
              
              # genarated dashbaod chart
              st.subheader("Generated Chart:")

              #needfull recomendation for genarated chat

              local_vars = {"df":df, "px": px}
              #exec => ececute , globals => global variable, local_vars => local variable 
              exec(generated_code, globals(), local_vars)

              if "fig" in local_vars:
                  st.plotly_chart(local_vars["fig"], use_container_width=True)
                  
              with st.expander("Show the generated code"):
                  st.code(generated_code, language="python")
              

            except Exception as e:
                print("Error generating code:", e)
           


