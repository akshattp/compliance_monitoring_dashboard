# GlobalPay AML Compliance Dashboard

Welcome to the GlobalPay AML Compliance Dashboard. This project has been migrated from Streamlit to a modern Angular 17 (Frontend) and FastAPI (Backend) architecture.

## Repository Structure
- `migration_output/`: Contains the modernized application.
  - `frontend/`: Angular 17 User Interface.
  - `backend/`: FastAPI Python Backend.
- `Dashboard_V1-1/`: The legacy Streamlit application.
- `stitch_globalpay_aml_compliance_dashboard/`: Raw UI templates and design assets.

---

## How to Run the Application

To run the full stack, you will need two separate terminal windows.

### 1. Starting the Backend (FastAPI)

The backend handles file uploads, data processing, and serves API endpoints on port `8000`.

**Open a new terminal and run:**
```bash
cd migration_output/backend

# (Optional but recommended) Activate your virtual environment
# source venv/bin/activate

# Install requirements (if you haven't already)
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*The backend API will be available at `http://127.0.0.1:8000`*
*Interactive API docs available at `http://127.0.0.1:8000/docs`*

### 2. Starting the Frontend (Angular)

The frontend serves the user interface on port `4200` and automatically connects to the backend API.

**Open a second terminal and run:**
```bash
cd migration_output/frontend

# Install node modules (if you haven't already)
npm install

# Start the Angular development server
npm start
```
*The frontend application will open in your browser at `http://localhost:4200`*

---

## Verifying the Setup
1. Once both servers are running, open your browser to `http://localhost:4200`.
2. Look at the top navigation bar. You should see a **"Backend Connected"** green pill indicator confirming that the Angular frontend has successfully communicated with the FastAPI backend.
3. If it says "Backend Offline", ensure your `uvicorn` backend server is running on port 8000 without errors.

## Using the Dashboard
1. The app starts empty. Navigate to the top-right search/download area, or use the app's upload functionality to provide the dataset (e.g., `TXN LINE MIS`).
2. The data will be processed by FastAPI, creating a canonical dataset in memory.
3. Navigate between pages (HOME, TRANSACTION SUMMARY, FATF, etc.) to view insights. All dashboard pages consume this centralized dataset.
