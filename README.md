# AI-Enabled Library Management System

**UNAI TECH Virtual Internship Program 2026**  
**Domain:** Full Stack Development  
**Project:** Project 08

## Overview
A web-based library management foundation for organizing books, students, borrowing, returns and reservations. Planned future enhancements include AI-powered book search and recommendations.

## Technology Stack
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Backend: Python Flask
- Database: MySQL
- Version control: Git and GitHub

## Project Structure
```text
AI-Library-Management-System/
├── backend/
│   ├── app.py
│   ├── templates/index.html
│   └── static/
│       ├── css/style.css
│       └── js/script.js
├── database/schema.sql
├── screenshots/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup (Windows PowerShell)
1. Install Python 3.10+, Git, MySQL Server and VS Code.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:
```powershell
py -m venv venv
venv\Scripts\Activate.ps1
```
4. Install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
5. Copy `.env.example` to `.env` and update local settings. Never commit `.env`.
6. Run `database/schema.sql` in MySQL Workbench or the MySQL command line.
7. Start Flask from the project root:
```bash
python backend/app.py
```
8. Open `http://127.0.0.1:5000` and verify `http://127.0.0.1:5000/health`.

## Day 1 Scope
Project structure, Flask starter app, initial MySQL schema, dependencies, documentation and Git/GitHub preparation.

**Note:** Database connection logic and application features are not implemented yet. The schema is prepared for subsequent development phases.

## Security
Never commit `.env` files, passwords, API keys or secret tokens.
