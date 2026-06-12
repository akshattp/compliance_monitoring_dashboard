Set-Location -Path $PSScriptRoot

# Install dependencies using the Python launcher on Windows.
py -m pip install -r requirements.txt

# Run the Streamlit app using the same Python launcher.
py -m streamlit run frontend/app.py
