import os
import sys
import traceback

# Add the project directory to the Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGL.settings')

def application(environ, start_response):
    status = '200 OK'
    output = b''
    
    try:
        from django.core.wsgi import get_wsgi_application
        django_app = get_wsgi_application()
        return django_app(environ, start_response)
    except Exception as e:
        status = '500 Internal Server Error'
        output = f"""
        Error loading Django application:
        
        {str(e)}
        
        Traceback:
        {traceback.format_exc()}
        
        Python path: {sys.path}
        
        Working directory: {os.getcwd()}
        """.encode('utf-8')
        
        headers = [
            ('Content-type', 'text/plain'),
            ('Content-Length', str(len(output)))
        ]
        
        start_response(status, headers)
        return [output]

# For debugging, you can run this directly
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, application)
    print("Serving on port 8000...")
    httpd.serve_forever()
