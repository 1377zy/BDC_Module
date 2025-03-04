from app import create_app

app = create_app()
app.config['TESTING'] = True
client = app.test_client()

with app.app_context():
    # Try to access the register page
    response = client.get('/auth/register')
    print(f"Status code: {response.status_code}")
    print(f"Response data: {response.data}")
    
    # Check if there's any before_request handler that might be blocking access
    print("\nChecking for before_request handlers:")
    for func in app.before_request_funcs.get(None, []):
        print(func.__name__)
    
    for blueprint_name, funcs in app.before_request_funcs.items():
        if blueprint_name is not None and funcs:
            for func in funcs:
                print(f"{blueprint_name}: {func.__name__}")
