# Windows Setup Instructions

## Prerequisites
1. Install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. Install Microsoft Visual C++ Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
3. Install Git from [git-scm.com](https://git-scm.com/download/win)
4. Install Tesseract OCR from [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
5. Install Poppler for Windows from [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)

## Setup Steps

### 1. Clone the Repository
```
git clone https://github.com/yourusername/book-knowledge-ai.git
cd book-knowledge-ai
```

### 2. Create Virtual Environment
Open PowerShell as Administrator and run:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Upgrade pip
```powershell
python -m pip install --upgrade pip
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Set Environment Variables
Add Tesseract and Poppler to your PATH or set them in your code:
```powershell
$env:PATH += ";C:\Program Files\Tesseract-OCR;C:\path\to\poppler\bin"
```

### 6. Start the Application
```powershell
streamlit run app.py
```

## Troubleshooting
See the windows-setup-guide.txt file for common issues and their solutions.