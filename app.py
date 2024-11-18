import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pandasai import SmartDatalake
from pandasai.llm.azure_openai import AzureOpenAI
import io
import matplotlib.pyplot as plt
from htmlTemplates import css, bot_template, user_template  # Import templates for styling
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from PIL import Image
import tempfile
import os
load_dotenv()

# Function to load and encode images as base64
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Image file not found: {file_path}")
        return None

# Load bot and user images
bot_image_base64 = get_img_as_base64("bot.png")
user_image_base64 = get_img_as_base64("user.png")

# Initialize the LLM with Azure OpenAI credentials
try:
    llm = AzureOpenAI(
        api_token="7wAFk647hvJJHdzHZgsqCD7SpS5lQKhpYGKKd5PUNFuaEU36DKjuJQQJ99AKACHrzpqXJ3w3AAABACOGhfA1",
        azure_endpoint="https://10000-m38m3nyg-northcentralus.openai.azure.com/",
        api_version="2024-02-15-preview",
        deployment_name="gpt-4"
    )
except Exception as e:
    st.error(f"Failed to initialize Azure OpenAI LLM: {e}")
    llm = None  # Set llm to None if initialization fails

# Set page configuration
st.set_page_config(layout="wide", page_title="Medical Insights BOT")

# Inject custom CSS
st.markdown(css, unsafe_allow_html=True)

# Sidebar for app info, features, file upload, and PDF download
with st.sidebar:
    st.markdown("<h1 style='color: orange;'>Medical Insights BOT</h1>", unsafe_allow_html=True)
    st.write("An intuitive application that allows you to interact with your data using natural language.")

    # File uploader
    uploaded_csv_file = st.file_uploader("Upload a file for analysis", type=['csv', 'xlsx', 'xls'])

    # Check if a file is uploaded and load data
    if uploaded_csv_file is not None:
        try:
            # Load the file if it's newly uploaded
            if uploaded_csv_file.name.endswith('csv'):
                st.session_state.dataframes = pd.read_csv(uploaded_csv_file)
                st.write("CSV file uploaded successfully!")
            else:
                sheets_dict = pd.read_excel(uploaded_csv_file, sheet_name=None)
                st.session_state.dataframes = [df.reset_index(drop=True) for df in sheets_dict.values()]
                st.write("Excel file uploaded successfully!")
        except Exception as e:
            st.error(f"Error loading file: {e}")
            st.session_state.dataframes = None  # Ensure dataframes are reset on failure
    
    st.markdown("### Features")
    st.markdown("""
    - **Conversational AI**: Converts natural language into actionable insights.
    - **Data Analysis Integration**: Enables interaction with uploaded data files for detailed analysis.
    - **Dynamic Responses**: Retains context for seamless conversations.
    """, unsafe_allow_html=True)
    
    
    def generate_pdf(chat_history):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y_position = height - 50  # Start from a bit lower than the top
        left_padding = 40  # Left margin padding
        right_padding = 40  # Right margin padding
        table_width_max = width - left_padding - right_padding
        max_text_width = width - left_padding - right_padding  # Max width for text lines

        # Title for the PDF
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_padding, y_position, "Chat Summary with MIBO")
        y_position -= 50  # Increase space after the title

        # Prepare styles for table cells and wrapped text
        styles = getSampleStyleSheet()
        wrap_style = ParagraphStyle(name="WrappedText", fontSize=8, leading=10, spaceAfter=6)
        text_wrap_style = ParagraphStyle(name="TextWrap", fontSize=10, leading=12, spaceAfter=6, alignment=0)  # Left-aligned text

        # Add chat messages to the PDF
        c.setFont("Helvetica", 11)  # Set a consistent font size
        for message in chat_history:
            role = "User" if message["role"] == "user" else "Assistant"
            
            # Draw role label
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left_padding, y_position, f"{role}:")
            y_position -= 20  # Space after role label

            # Render DataFrame content
            if isinstance(message["content"], pd.DataFrame):
                df = message["content"]
                max_rows_per_page = 30  # Define maximum rows to fit per page
                num_pages = (len(df) // max_rows_per_page) + 1
                
                for page in range(num_pages):
                    # Get chunk of DataFrame for the current page
                    chunk_df = df.iloc[page * max_rows_per_page:(page + 1) * max_rows_per_page]
                    data = [[Paragraph(str(cell), wrap_style) for cell in row] for row in [chunk_df.columns.to_list()] + chunk_df.values.tolist()]
                    table = Table(data, colWidths=[table_width_max / len(chunk_df.columns)] * len(chunk_df.columns))
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
                    ]))

                    # Calculate space needed for the table and apply left and right padding
                    table_width, table_height = table.wrap(0, 0)
                    x_position = left_padding  # Start drawing from the left margin
                    if y_position - table_height < 50:
                        c.showPage()
                        y_position = height - 50
                    y_position -= table_height
                    table.drawOn(c, x_position, y_position)
                    y_position -= 30

                    if page < num_pages - 1:  # Prepare for the next chunk
                        c.showPage()
                        y_position = height - 50

            # Render chart content
            elif isinstance(message["content"], plt.Figure):
                chart_height = 220
                if y_position - chart_height < 50:  # Check if chart fits on the current page
                    c.showPage()
                    y_position = height - 50
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                    message["content"].savefig(tmpfile.name, format="png")
                    c.drawImage(tmpfile.name, 60, y_position - chart_height, width=440, height=200)  # Centered horizontally
                    y_position -= chart_height + 30  # Adjust for chart height and extra space
                os.remove(tmpfile.name)  # Delete temporary file after use

            # Render image content
            elif isinstance(message["content"], io.BytesIO):
                img_height = 220
                if y_position - img_height < 50:  # Check if image fits on the current page
                    c.showPage()
                    y_position = height - 50
                image = Image.open(message["content"])
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                    image.save(tmpfile.name, format="PNG")
                    c.drawImage(tmpfile.name, 60, y_position - img_height, width=440, height=200)  # Centered horizontally
                    y_position -= img_height + 30  # Adjust for image height and extra space
                os.remove(tmpfile.name)  # Delete temporary file after use

            # Render text content with wrapping
            elif isinstance(message["content"], str):
                content = message["content"]
                paragraph = Paragraph(content, text_wrap_style)  # Create a Paragraph with wrapping
                paragraph_width, paragraph_height = paragraph.wrap(max_text_width, y_position)  # Wrap within max width
                if y_position - paragraph_height < 50:  # Check if it fits on the page
                    c.showPage()
                    y_position = height - 50
                paragraph.drawOn(c, left_padding, y_position - paragraph_height)  # Draw the paragraph
                y_position -= paragraph_height + 30  # Adjust for paragraph height and spacing

            # Add a new page if space runs out
            if y_position < 50:
                c.showPage()
                y_position = height - 50

        c.save()
        buffer.seek(0)
        return buffer
    # Download chat history as PDF
    st.markdown("### Download Options")
    if st.button("Download Chat as PDF"):
        if "chat_history" in st.session_state and st.session_state.chat_history:
            pdf_buffer = generate_pdf(st.session_state.chat_history)
            st.download_button(
                label="Download Chat PDF",
                data=pdf_buffer,
                file_name="MIBO_Insights_Report.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("No chat history to download.")



# Initialize session state for chat history and dataframes
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I'm MIBO your Medical Insights BOT. Please upload a file to get started!"}
    ]
if "dataframes" not in st.session_state:
    st.session_state.dataframes = None

# Main content area
st.title("Chat with Medical Insights BOT")

# Initialize SmartDatalake with dataframes and LLM if a file is uploaded and llm is available
sdf = None  # Initialize sdf as None by default
if st.session_state.dataframes is not None and llm is not None:
    try:
        sdf = SmartDatalake(st.session_state.dataframes, config={"llm": llm})
    except Exception as e:
        st.error(f"Failed to initialize SmartDatalake with the provided data: {e}")

# Container for chat history
response_container = st.container()
# Container for input area
input_container = st.container()

# Display chat history using the custom templates with images
with response_container:
    for message in st.session_state.chat_history:
        try:
            if message["role"] == "assistant":
                content = message["content"]
                if isinstance(content, pd.DataFrame):
                    st.markdown(f"<div style='text-align: left;'><b>Assistant:</b></div>", unsafe_allow_html=True)
                    st.dataframe(content)  # Display as table
                elif isinstance(content, plt.Figure):
                    st.markdown(f"<div style='text-align: left;'><b>Assistant:</b></div>", unsafe_allow_html=True)
                    st.pyplot(content)  # Display the chart directly
                elif isinstance(content, str) and content.endswith('.png'):
                    # Load and display the image from file path if necessary
                    try:
                        with open(content, "rb") as img_file:
                            st.image(img_file, caption="Generated Image")
                    except Exception as e:
                        st.error(f"Could not load the image: {e}")
                elif isinstance(content, io.BytesIO):
                    st.markdown(f"<div style='text-align: left;'><b>Assistant:</b></div>", unsafe_allow_html=True)
                    st.image(content, caption="Generated Image")  # Display as in-memory image
                else:
                    # Display assistant text with bot image
                    st.markdown(bot_template.replace("{{MSG}}", content).replace("{{URL}}", bot_image_base64), unsafe_allow_html=True)
            else:
                # Display user text with user image
                st.markdown(user_template.replace("{{MSG}}", message["content"]).replace("{{URL}}", user_image_base64), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying chat message: {e}")

# Input area for user
with input_container:
    if sdf is None:
        st.info("Please upload a file to enable the chat.")
    else:
        user_input = st.chat_input("Type your question here...")
        if user_input:
            try:
                # Process user input if sdf is initialized
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Generate assistant response using LLM
                with st.spinner("Generating response..."):
                    response = sdf.chat(user_input)  # Assume response can be text, DataFrame, Figure, or image bytes

                # Check if response is empty or has a specific error message
                if isinstance(response, str) and "No code found in the response" in response:
                    response = "I'm sorry, I couldn't understand the question. Could you please rephrase it?"
                elif isinstance(response, pd.DataFrame) and response.empty:
                    response = "The result is empty. Could you please rephrase your question to get more meaningful results?"

                # Append assistant response to chat history
                if isinstance(response, pd.DataFrame):
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                elif isinstance(response, plt.Figure):
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                elif isinstance(response, io.BytesIO):
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                elif isinstance(response, str) and response.endswith('.png'):
                    # If response is a file path, convert it to in-memory image
                    try:
                        with open(response, "rb") as img_file:
                            image_bytes = io.BytesIO(img_file.read())
                            st.session_state.chat_history.append({"role": "assistant", "content": image_bytes})
                    except Exception as e:
                        st.session_state.chat_history.append({"role": "assistant", "content": "Unable to load the image file."})
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": str(response)})
                
                # Refresh to display updated chat history
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error processing user input or generating response: {e}")

# Apply custom sidebar color
st.markdown("""
    <style>
        [data-testid=stSidebar] {
            background-color: #43316d;
        }
    </style>
    """, unsafe_allow_html=True)
