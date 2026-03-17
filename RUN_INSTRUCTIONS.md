# AI-Driven Personal Preference Identifier - Setup Guide

This guide provides step-by-step instructions to set up and run the project on a new computer.

## Prerequisites

Ensure you have the following installed on your system:
1.  **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
2.  **MySQL Server**: [Download MySQL](https://dev.mysql.com/downloads/installer/) (Recommended: MySQL Community Server & MySQL Workbench)

---

## Step-by-Step Installation

### 1. Clone or Copy the Project
Transfer the project folder to the target machine.

### 2. Set Up a Virtual Environment
Open a terminal (PowerShell or Command Prompt) in the project root directory (`.../p_system`) and run:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
With the virtual environment activated, install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Database Configuration

1.  **Open MySQL Workbench** (or your preferred MySQL client).
2.  **Create a new database**:
    ```sql
    CREATE DATABASE preference_db;
    ```
3.  **Configure Environment Variables**:
    Create a file named `.env` in the `p_system` directory (if it doesn't exist) and add the following:
    ```env
    DB_NAME=preference_db
    DB_USER=root
    DB_PASSWORD=your_mysql_password
    DB_HOST=localhost
    DB_PORT=3306
    DJANGO_SECRET_KEY=generate-a-new-random-key-here
    DJANGO_DEBUG=True
    ```
    > [!IMPORTANT]
    > **For XAMPP users**: 
    > 1. Start **Apache** and **MySQL** modules from the XAMPP Control Panel.
    > 2. By default, the `DB_PASSWORD` for `root` is empty. Leave it blank in your `.env` file: `DB_PASSWORD=`
    > 3. Replace `your_mysql_password` with your actual MySQL password if you have set one.

### 5. Database Setup & Data Population

#### Option A: Full Automated Setup (Single Command)
Run this single command to handle migrations, create the catalog, and precompute AI features:
```bash
python manage.py makemigrations preference_app && python manage.py migrate && python populate_jewelry_questions.py && python generate_catalog.py && python precompute_catalog_features.py
```

#### Option B: Sequential Steps
If you prefer to run them one-by-one:

1.  **Run Migrations**:
    ```bash
    python manage.py makemigrations preference_app
    python manage.py migrate
    ```

2.  **Seed Initial Data (SQL Script)**:
    ```bash
    mysql -u root -p preference_db < database/seed_questions.sql
    ```

3.  **Populate Survey Questions**:
    ```bash
    python populate_jewelry_questions.py
    ```

4.  **Generate Product Catalog**:
    ```bash
    python generate_catalog.py
    ```

5.  **Precompute AI Features**:
    ```bash
    python precompute_catalog_features.py
    ```

### 6. Create Admin Account
Create a staff account to access the admin dashboard (this is interactive):
```bash
python manage.py createsuperuser
```

### 7. Start the Development Server
Run the project:
```bash
python manage.py runserver
```

### 7. Access the Application
Open your web browser and go to:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Troubleshooting

- **mysqlclient Installation Error**: If you face issues installing `mysqlclient`, ensure you have the [MySQL Connector/C](https://dev.mysql.com/downloads/connector/c/) installed or use a pre-compiled binary.
- **Environment Variables**: Double-check your `.env` file if the database connection fails.
