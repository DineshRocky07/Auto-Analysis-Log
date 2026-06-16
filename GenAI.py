import streamlit as st
import pandas as pd
from google import genai
import plotly.express as px
import os
import time   #face error free remove time and use this for loading display

# create session state for suggestions to memory all suggestions and st.session_state is small memory 
if "suggestions"not in st.session_state:
    st.session_state["suggestions"] = []
if "last_uploaded_file" not in st.session_state:
    st.session_state["last_uploaded_file"] = ""

#main config page
st.set_page_config(page_title="oneClick Dashboard", layout="wide")

with st.sidebar:
     st.title("Settings")
     api_key=st.text_input("Enter your Google GenAI API Key", type="password")

if not api_key:
    st.warning("Please enter your Google GenAI API Key to continue.")
    st.stop()
client =genai.Client(api_key=api_key)


st.title("OneClick AI Dashboard")
st.write("Upload your data, and let the AI build your dashboard instantly.")


uploaded_file =st.file_uploader("Upload your CSV file", type=["csv"])   

if uploaded_file is not None:
    df =pd.read_csv(uploaded_file)
    coloum =list(df.columns)
    if st.session_state["last_uploaded_file"] != uploaded_file.name:
        st.session_state["suggestions"] = []  # Clear previous suggestions when a new file is uploaded
        st.session_state["last_uploaded_file"] = uploaded_file.name  # Update the last uploaded file name
    # UI
    with st.expander("Peek at your raw data Preview"):
         st.write(f"colums: {coloum}")
         st.dataframe(df.head(4))
    st.divider() 

    col1,col2 =st.columns([1,2.5])

    with col1:
         st.subheader("control panel")
        # 1. Ask the AI for ideas
         if st.button("Auto-Analyze Dataset",use_container_width=True):
            #spinner loading display
            with st.spinner("AI is thinking of 5 chart ideas..."):
                #colum names and import name must menctioned in the prompt
                brainstorm_prompt="""
                Look at these columns: {coloum}. 
                Suggest 5 interesting charts to build. 
                Return ONLY the names of the charts separated by a pipe character '|'. 
                Example: Sales Pie Chart | Region Bar Chart | Profit Line Chart
                """
                try:
                    # call llm 
                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                            contents=brainstorm_prompt
                    )
                    raw_text=response.text.strip()

                    # Save the 5 ideas into our locked safe!
                    st.session_state["suggestions"]= raw_text.split("|") 

                except Exception as e:
                    if "429" in str(e):
                        st.warning("⏳ Google's Free Tier speed limit reached! Please wait 60 seconds and try again.")
                    else:
                        st.error(f"An unexpected error occurred: {e}")
                #create a emptycard
         selected_ideas = []
         if len(st.session_state["suggestions"]) >0:
                  st.write("### AI Suggestions:")
                  st.info("Tick the boxes, then click Generate!")

                  #loop Draw a tick box 
                  for idea in st.session_state["suggestions"]:
                      is_ticked =st.checkbox(idea)
                      if is_ticked:
                           selected_ideas.append(idea)

                  if len(selected_ideas) > 0:
                      generate_clicked =st.button("Generate Selected Charts", type="primary", use_container_width=True)
    with col2:
            st.subheader("Your Dashboard")
            if len(selected_ideas) >0 and 'generate_clicked' in locals() and generate_clicked:
                      #draw a button for each idea
                        for idea in selected_ideas:
                              custom_prompt = f"""  
                                    You are an expert Python data analyst. I have a pandas DataFrame named 'df' with columns: {', '.join(coloum)}.
                                    Write Python code using `plotly.express` as `px` to create this specific chart: {idea}.
                                    Assign the resulting plotly figure to a variable named `fig`.
                                    Return ONLY the raw python code. Do not include markdown.
                                    """
                    
                                # 4. The Chef cooks the specific chart
                              with st.spinner(f"AI is cooking the {idea}..."):
                                    try:
                                        response =client.models.generate_content(
                                            model="gemini-3.5-flash",
                                            contents=custom_prompt
                                        )
                                        generated_code = response.text.strip()

                                        #when ai create markdown format code so use this remove that
                                        if generated_code.startswith("```python"):
                                                generated_code = generated_code[9:-3].strip()
                                        
                                        # Draw a clean box for each chart
                                        with st.container(border=True):
                                             st.write(f"**{idea}**")
                                             # genarated dashbaod chart
                                             #needfull recomendation for genarated chart
                                             local_vars = {"df":df, "px": px}
                                                #exec => ececute , globals => global variable, local_vars => local variable 
                                             exec(generated_code, globals(), local_vars)

                                             if "fig" in local_vars:
                                                st.plotly_chart(local_vars["fig"], use_container_width=True)
                                                                            
                                             with st.expander("Show the generated code"):
                                                st.code(generated_code, language="python")
                                        time.sleep(4)
                                    except Exception as e:
                                        #if server is too crowded and give 503 error so use this
                                        if "503" in str(e):
                                            st.warning(f"⏳ Google's servers are too crowded right now to build '{idea}'. Please try this specific chart again in a few minutes!")
                                        else:
                                            # For any other weird errors:
                                            st.error(f"Error generating {idea}: {e}")
                                    
