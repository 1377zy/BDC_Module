import requests
from bs4 import BeautifulSoup

# Start a session
session = requests.Session()

# Get the login page to get the CSRF token
login_url = 'http://127.0.0.1:5000/auth/login'
login_response = session.get(login_url)
login_soup = BeautifulSoup(login_response.text, 'html.parser')
csrf_token = login_soup.find('input', {'id': 'csrf_token'})['value']

# Login with admin credentials
login_data = {
    'csrf_token': csrf_token,
    'username': 'admin',
    'password': 'admin123',
    'remember_me': 'y'
}
login_post_response = session.post(login_url, data=login_data, allow_redirects=True)

# Check if login was successful
if 'You have been logged in successfully!' in login_post_response.text:
    print('Login successful')
else:
    print('Login failed')
    print(login_post_response.text)

# Try to access the register page
register_url = 'http://127.0.0.1:5000/auth/register'
register_response = session.get(register_url)

# Check if we can access the register page
if register_response.status_code == 200:
    print('Register page accessible')
    register_soup = BeautifulSoup(register_response.text, 'html.parser')
    title = register_soup.find('title')
    print(f'Page title: {title.text if title else "No title found"}')
else:
    print(f'Register page not accessible, status code: {register_response.status_code}')
    print(register_response.text)
