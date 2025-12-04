# SpenZo - Smart Expense Tracker

A Flask-based web application for tracking and managing personal expenses with bill upload, categorization, and reporting features.

## Features

- ✅ **User Authentication** - Secure registration and login system
- ✅ **Bill Upload** - Upload bills in PDF, Image, or CSV format
- ✅ **AI-Powered Categorization** - Automatic bill categorization using Google Gemini AI
- ✅ **Manual Entry** - Add expenses manually with custom categories
- ✅ **Dashboard** - Visual overview with charts and statistics
- ✅ **Category Management** - View expenses by category
- ✅ **Transaction Reports** - Complete history of all transactions with remarks
- ✅ **Reminders** - Set reminders for upcoming payments
- ✅ **Talky Assistant** - AI-powered expense query assistant
- ✅ **Mobile Responsive** - Works seamlessly on phones and desktops
- ✅ **User Isolation** - Each user sees only their own data

## Recent Fixes

All major issues have been resolved:

1. ✅ **Report functionality** - Now shows complete transaction history
2. ✅ **User data isolation** - Each user has their own isolated data
3. ✅ **Mobile responsiveness** - Fully responsive design for all devices
4. ✅ **Deployment ready** - Documentation and configuration for deployment

See `FIXES_SUMMARY.md` for detailed information about all fixes.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd nb
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Create a `.env` file or set `SECRET_KEY` environment variable
   - Update Google Gemini API key in `app.py` (line 24)

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open your browser and go to `http://localhost:5000`
   - Register a new account or login

## Database Schema

The application uses SQLite with the following tables:

- **users** - User accounts (id, name, username, password, age, created_at)
- **bill_items** - Expense records (id, user_id, bill_filename, item, category, amount, date, remark)
- **reminders** - Payment reminders (id, user_id, title, description, amount, due_date)

## Deployment

**Important:** This Flask application cannot be deployed on GitHub Pages (static hosting only).

See `DEPLOYMENT.md` for detailed deployment instructions. Recommended platforms:
- **Render** (Free tier available) - Recommended
- **Railway** (Free tier available)
- **PythonAnywhere** (Free tier available)
- **Heroku** (Paid)

## Project Structure

```
nb/
├── app.py                 # Main Flask application
├── extensions.py          # Flask extensions
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── bills.db              # SQLite database
├── templates/            # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── report.html
│   ├── login.html
│   ├── register.html
│   └── ...
├── static/               # CSS and static files
├── uploads/             # Uploaded bill files
├── DEPLOYMENT.md        # Deployment guide
└── FIXES_SUMMARY.md     # Summary of fixes
```

## Usage

1. **Register/Login** - Create an account or login
2. **Add Expenses** - Upload bills or add manually
3. **View Dashboard** - See your expense overview
4. **View Reports** - Check complete transaction history
5. **Manage Categories** - Organize expenses by category
6. **Set Reminders** - Never miss a payment

## Security Notes

- User data is isolated by `user_id`
- Passwords are hashed using Werkzeug
- Session-based authentication
- All routes are protected with `@require_login` decorator

## Requirements

- Python 3.8+
- Flask 2.3.3+
- Google Gemini API key
- See `requirements.txt` for complete list

## License

This project is open source and available for personal use.

## Support

For deployment help, see `DEPLOYMENT.md`.
For information about fixes, see `FIXES_SUMMARY.md`.

---

**Note:** Make sure to change the `SECRET_KEY` in production and keep your API keys secure!


```
📦 
├─ .gitignore
├─ DEPLOYMENT.md
├─ FIXES_SUMMARY.md
├─ Procfile
├─ README.md
├─ __pycache__
│  └─ extensions.cpython-312.pyc
├─ app.py
├─ bills.db
├─ extensions.py
├─ instance
│  └─ spenzo.db
├─ requirements.txt
├─ static
│  ├─ frist.css
│  ├─ img1.png
│  ├─ img2.png
│  ├─ login.css
│  ├─ register.css
│  └─ style.css
├─ templates
│  ├─ add_category.html
│  ├─ add_reminder.html
│  ├─ base.html
│  ├─ category.html
│  ├─ dashboard.html
│  ├─ details.html
│  ├─ edit.html
│  ├─ frist.html
│  ├─ home.html
│  ├─ index.html
│  ├─ login.html
│  ├─ register.html
│  ├─ report.html
│  └─ talky.html
└─ uploads
   ├─ 1 (1).webp
   ├─ Food1691490180122.png
   ├─ Screenshot 2025-11-11 184946.pdf
   ├─ WhatsApp Image 2025-11-10 at 20.48.13_db5cb95d.jpg
   ├─ slip 5th sem 2nd.pdf
   ├─ slip.pdf
   └─ test.pdf
```
©generated by [Project Tree Generator](https://woochanleee.github.io/project-tree-generator)

