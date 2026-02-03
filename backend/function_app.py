import azure.functions as func
import logging
from app.main import app as fastapi_app

# Create Azure Functions app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="HttpTrigger")
@app.route(route="{*route}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Azure Functions HTTP trigger that wraps FastAPI"""
    
    logging.info(f'Processing request: {req.method} {req.url}')
    
    # Import AsgiMiddleware to wrap FastAPI app
    from azure.functions.extension.http.fastapi import Request, StreamingResponse
    import asyncio
    
    # Create ASGI scope from Azure Functions request
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": req.method,
        "scheme": "https",
        "path": req.url.split("?")[0].replace("/api/HttpTrigger", ""),
        "query_string": req.url.split("?")[1].encode() if "?" in req.url else b"",
        "headers": [(k.encode(), v.encode()) for k, v in req.headers.items()],
        "server": ("eagle-harbor-backend.azurewebsites.net", 443),
    }
    
    # Get response from FastAPI
    try:
        from starlette.testclient import TestClient
        client = TestClient(fastapi_app)
        
        path = req.route_params.get("route", "")
        full_path = f"/{path}" if path else "/"
        
        if req.method == "GET":
            response = client.get(full_path, params=dict(req.params))
        elif req.method == "POST":
            response = client.post(full_path, json=req.get_json() if req.get_body() else None)
        elif req.method == "PUT":
            response = client.put(full_path, json=req.get_json() if req.get_body() else None)
        elif req.method == "DELETE":
            response = client.delete(full_path)
        else:
            response = client.request(req.method, full_path)
        
        return func.HttpResponse(
            body=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            mimetype=response.headers.get("content-type", "application/json")
        )
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            body=str(e),
            status_code=500
        )
