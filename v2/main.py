import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pandasai import SmartDataframe, SmartDatalake
from pandasai.llm.azure_openai import AzureOpenAI
import io
import platform
import psutil
import subprocess
import time

load_dotenv()

# llm = AzureOpenAI(
#     api_token="8IWnAtKa3pgBbFEZuatFbQYR7kxzBUWZ9KatcDmDdqCy3pElxl4DJQQJ99AKACYeBjFXJ3w3AAABACOG2wwI",
#     azure_endpoint="https://hex-ds-genai-pilots.openai.azure.com/",
#     api_version="2024-02-15-preview",
#     deployment_name="gpt-4o-hex-ds"
# )
llm = AzureOpenAI(
    api_token="7wAFk647hvJJHdzHZgsqCD7SpS5lQKhpYGKKd5PUNFuaEU36DKjuJQQJ99AKACHrzpqXJ3w3AAABACOGhfA1",
    azure_endpoint="https://10000-m38m3nyg-northcentralus.openai.azure.com/",
    api_version="2024-02-15-preview",
    deployment_name="gpt-4"
)
#https://10000-m38m3nyg-northcentralus.openai.azure.com/
#7wAFk647hvJJHdzHZgsqCD7SpS5lQKhpYGKKd5PUNFuaEU36DKjuJQQJ99AKACHrzpqXJ3w3AAABACOGhfA1
#gpt-4

def close_image_viewer():
    system = platform.system()

    if system == "Windows":
        possible_viewers = ["Microsoft.Photos.exe", "PhotosApp.exe"]
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in possible_viewers:
                    proc.terminate()
                    time.sleep(0.5)
                    if proc.is_running():
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    elif system == "Darwin":
        try:
            subprocess.run(["pkill", "Preview"], check=True)
        except subprocess.CalledProcessError:
            pass

    elif system == "Linux":
        possible_viewers = ["eog", "feh", "gpicview"]
        for viewer in possible_viewers:
            try:
                subprocess.run(["pkill", viewer], check=True)
            except subprocess.CalledProcessError:
                pass

st.set_page_config(layout="wide", page_title="MSL Insights Assistant")
st.title("MSL Insights Assistant")

uploaded_csv_file = st.file_uploader("Upload a file for analysis", type=['csv', 'xlsx', 'xls'])

if uploaded_csv_file is not None:
    if uploaded_csv_file.name.endswith('csv'):
        dataframes = pd.read_csv(uploaded_csv_file)
        st.write("Uploaded CSV File:")
        st.dataframe(dataframes, use_container_width=True)  # Ensures full-width display
    else:
        sheets_dict = pd.read_excel(uploaded_csv_file, sheet_name=None)
        
        # Display each sheet's DataFrame with an expander and full-width adjustment
        dataframes = []
        for i, (sheet_name, df) in enumerate(sheets_dict.items(), start=1):
            globals()[f"df{i}"] = df  # Assign each dataframe as a global variable
            with st.expander(f"Sheet name: {sheet_name} (Accessible as df{i})"):
                st.dataframe(df, height=600, use_container_width=True)  # Full-width display
            dataframes.append(df)

    sdf = SmartDatalake(dataframes, config={"llm": llm})

    prompt = st.text_area("Enter your prompt")

    if st.button("Generate"):
        if prompt:
            with st.spinner("Generating Response..."):
                response = sdf.chat(prompt)

                if isinstance(response, str) and response.endswith(('.png', '.jpg', '.jpeg')):
                    with open(response, "rb") as file:
                        image_bytes = file.read()  
                    st.image(io.BytesIO(image_bytes), caption="Generated Image", use_container_width=True)
                    close_image_viewer()  
                    st.download_button(
                    label="Download Image",
                    data=image_bytes,
                    file_name="generated_image.png",
                    mime="image/png"
                )
                elif isinstance(response, io.BytesIO):
                    st.image(response, caption="Generated Graph", use_container_width=True)
                    close_image_viewer()
                    st.download_button(
                    label="Download Image",
                    data=response.getvalue(),
                    file_name="generated_graph.png",
                    mime="image/png"
                )
                else:
                    st.success("Response:")
                    st.write(response)
                    # Download response as text file
                    if isinstance(response, pd.DataFrame):
                        # Convert DataFrame to CSV for download
                        csv = response.to_csv(index=False)
                        st.download_button(
                            label="Download response as CSV",
                            data=csv,
                            file_name="response.csv",
                            mime="text/csv"
                        )
                    else:
                        # For text responses, download as .txt
                        response_text = str(response)
                        st.download_button(
                            label="Download response as Text",
                            data=response_text,
                            file_name="response.txt",
                            mime="text/plain"
                        )
        else:
            st.warning("Please enter a prompt")
else:
    st.info("Upload a file to get started.")
