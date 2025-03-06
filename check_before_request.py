from app import create_app

app = create_app()

print("Before request handlers:")
for func in app.before_request_funcs.get(None, []):
    print(func.__name__)

for blueprint_name, funcs in app.before_request_funcs.items():
    if blueprint_name is not None:
        for func in funcs:
            print(f"{blueprint_name}: {func.__name__}")
