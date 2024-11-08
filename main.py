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

llm = AzureOpenAI(
    api_token="8IWnAtKa3pgBbFEZuatFbQYR7kxzBUWZ9KatcDmDdqCy3pElxl4DJQQJ99AKACYeBjFXJ3w3AAABACOG2wwI",
    azure_endpoint="https://hex-ds-genai-pilots.openai.azure.com/",
    api_version="2024-02-15-preview",
    deployment_name="gpt-35-hex-ds"
)

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
st.set_page_config(layout="wide",page_title="MSL Insights Assistant")
st.title("MSL Insights Assistant")

uploaded_csv_file = st.file_uploader("Upload a file for analysis", type=['csv','xlsx','xls'])

if uploaded_csv_file is not None:
    if uploaded_csv_file.name.endswith('csv'):
        dataframes = pd.read_csv(uploaded_csv_file)
    else:
        # df = pd.read_excel(uploaded_csv_file)
        sheets_dict = pd.read_excel(uploaded_csv_file, sheet_name=None)
        # Dynamically create global variables for each sheet (df1, df2, etc.)
        for i, (sheet_name, df) in enumerate(sheets_dict.items(), start=1):
            globals()[f"df{i}"] = df  # Assign each dataframe as a global variable
            st.write(f"Sheet name: {sheet_name} (Accessible as df{i})")
            st.write(df)

        # Collect all created df1, df2, etc., variables dynamically
        dataframes = [globals()[f"df{i}"] for i in range(1, len(sheets_dict) + 1)]
        # Pass the dynamically collected global variables to SmartDataframe
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
                elif isinstance(response, io.BytesIO):
                    st.image(response, caption="Generated Graph", use_container_width=True)
                    close_image_viewer()
                else:
                    st.success("Response:")
                    st.write(response)
        else:
            st.warning("Please enter a prompt")
else:
    st.info("Upload a file to get started.")
