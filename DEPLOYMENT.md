# Deployment Guide for SpenZo Expense Tracker

## Important: GitHub Pages Limitation

**GitHub Pages only supports static websites** (HTML, CSS, JavaScript). Your Flask application is a **dynamic web application** that requires:
- A Python runtime environment
- A web server (like Gunicorn, uWSGI, or Waitress)
- Database support (SQLite in your case)
- Server-side processing

**Therefore, GitHub Pages cannot host your Flask application directly.**

## Recommended Deployment Options

### Option 1: Render (Recommended - Free Tier Available)
**Best for:** Quick deployment with free hosting

1. **Create a GitHub repository** and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/RahulB38/Spenzo
   git push -u origin main
   ```

2. **Sign up at [Render.com](https://render.com)** (free account)

3. **Create a new Web Service:**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment: Python 3
   - Add environment variable: `FLASK_ENV=production`

4. **Your app will be live** at `https://your-app-name.onrender.com`

### Option 2: Railway (Free Tier Available)
**Best for:** Easy deployment with database support

1. **Sign up at [Railway.app](https://railway.app)**

2. **Create a new project** and connect your GitHub repo

3. **Railway will auto-detect Flask** and deploy automatically

4. **Add PostgreSQL** (free tier) if you want a production database

### Option 3: Heroku (Paid, but has free alternatives)
**Note:** Heroku removed their free tier, but you can use alternatives

1. **Create a `Procfile`** in your project root:
   ```
   web: gunicorn app:app
   ```

2. **Create a `runtime.txt`**:
   ```
   python-3.11.0
   ```

3. **Deploy via Heroku CLI** or GitHub integration

### Option 4: PythonAnywhere (Free Tier Available)
**Best for:** Learning and small projects

1. **Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)**

2. **Upload your files** via the web interface

3. **Configure WSGI** file to point to your Flask app

4. **Your app will be live** at `https://YOUR_USERNAME.pythonanywhere.com`

## Required Changes for Production

Before deploying, make these changes:

### 1. Update `app.py` for Production

Add this at the end of `app.py`:

```python
if __name__ == "__main__":
    # For production, use gunicorn or waitress
    # For development only:
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

### 2. Create `Procfile` (for Heroku/Railway)

```
web: gunicorn app:app
```

### 3. Update Secret Key

**IMPORTANT:** Change the secret key in `app.py`:

```python
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this')
```

Set `SECRET_KEY` as an environment variable in your hosting platform.

### 4. Database Considerations

- **SQLite** works for small projects but has limitations
- For production, consider **PostgreSQL** or **MySQL**
- Update database connection in `app.py` if needed

### 5. Environment Variables

Set these in your hosting platform:
- `SECRET_KEY`: A random secret key for sessions
- `FLASK_ENV`: Set to `production`
- `PORT`: Usually auto-set by hosting platform

## Quick Start with Render (Recommended)

1. **Push code to GitHub**

2. **Go to Render Dashboard** → New → Web Service

3. **Connect GitHub repo**

4. **Configure:**
   - Name: `spenzo-expense-tracker`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. **Add Environment Variable:**
   - Key: `SECRET_KEY`
   - Value: (generate a random string)

6. **Deploy!**

Your app will be live in 2-3 minutes!

## Testing Locally Before Deployment

1. **Install gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Run locally:**
   ```bash
   gunicorn app:app
   ```

3. **Test at:** `http://localhost:8000`

## Need Help?

- Render Documentation: https://render.com/docs
- Railway Documentation: https://docs.railway.app
- Flask Deployment Guide: https://flask.palletsprojects.com/en/latest/deploying/

---

**Remember:** Always test your application thoroughly before deploying to production!

