from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

# Secrets codés en dur - VULNÉRABILITÉ
API_KEY = "sk-1234567890abcdef1234567890abcdef12345678"
DB_PASSWORD = "admin123!@#"
DATABASE_URL = f"sqlite:///products.db?password={DB_PASSWORD}"

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vulnerable App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .search-box { margin: 20px 0; }
            input[type="text"] { padding: 8px; width: 300px; }
            input[type="submit"] { padding: 8px 16px; }
            .result { margin: 20px 0; padding: 10px; background: #f5f5f5; }
        </style>
    </head>
    <body>
        <h1>Product Search</h1>
        <div class="search-box">
            <form action="/search" method="GET">
                <input type="text" name="query" placeholder="Search products...">
                <input type="submit" value="Search">
            </form>
        </div>
        <p><strong>Warning:</strong> This application contains intentional vulnerabilities for testing purposes.</p>
    </body>
    </html>
    ''')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    
    if not query:
        return "Please provide a search query"
    
    try:
        # VULNÉRABILITÉ: Injection SQL directe (CWE-89)
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        
        # Création de la table si elle n'existe pas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL
        )
        ''')
        
        # Insertion de données de test
        cursor.execute('''
        INSERT OR IGNORE INTO products (name, description, price) VALUES
        ('Laptop', 'High-performance laptop', 999.99),
        ('Phone', 'Smartphone with camera', 699.99),
        ('Tablet', '10-inch tablet', 349.99)
        ''')
        
        # VULNÉRABILITÉ: Injection SQL - concaténation directe
        sql_query = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
        cursor.execute(sql_query)
        
        results = cursor.fetchall()
        conn.close()
        
        # Affichage des résultats
        result_html = render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Search Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .product { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
                .back-link { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Search Results for: {{ query }}</h1>
            <div class="back-link">
                <a href="/">← Back to search</a>
            </div>
            {% if results %}
                {% for product in results %}
                    <div class="product">
                        <h3>{{ product[1] }}</h3>
                        <p>{{ product[2] }}</p>
                        <p><strong>Price: ${{ product[3] }}</strong></p>
                    </div>
                {% endfor %}
            {% else %}
                <p>No products found.</p>
            {% endif %}
            <p><strong>Debug:</strong> SQL Query executed: {{ sql_query }}</p>
        </body>
        </html>
        ''', query=query, results=results, sql_query=sql_query)
        
        return result_html
        
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/admin')
def admin():
    # VULNÉRABILITÉ: Endpoint admin sans authentification
    api_info = {
        "api_key": API_KEY,
        "db_password": DB_PASSWORD,
        "database_url": DATABASE_URL
    }
    return f"Admin Panel - API Key: {API_KEY}, DB Password: {DB_PASSWORD}"

@app.route('/debug')
def debug():
    # VULNÉRABILITÉ: Information disclosure
    return render_template_string('''
    <h1>Debug Information</h1>
    <p>Environment variables:</p>
    <pre>{{ env_vars }}</pre>
    <p>Python version: {{ python_version }}</p>
    <p>Flask version: {{ flask_version }}</p>
    ''', env_vars=dict(os.environ), python_version=os.sys.version, flask_version=Flask.__version__)

if __name__ == '__main__':
    # VULNÉRABILITÉ: Mode debug activé en production
    app.run(host='0.0.0.0', port=5000, debug=True)
