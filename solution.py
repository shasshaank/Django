import time
import json
from django.http import JsonResponse

class ChaosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_superuser:
            return self.get_response(request)
          
        delay_header = request.headers.get('X-Chaos-Delay')
        if delay_header:
            try:
                delay_seconds = int(delay_header) / 1000.0
                time.sleep(delay_seconds)
            except ValueError:
                pass
              
        if request.headers.get('X-Chaos-Mode') == '503':
            path_length = len(request.path)
            if path_length % 2 == 0:
                return JsonResponse(
                    {"error": "Chaos Injected"}, 
                    status=503
                )

        response = self.get_response(request)
      
        if request.headers.get('X-Chaos-Mutate') == 'True':

            if 'application/json' in response.get('Content-Type', ''):
                try:
                    content = json.loads(response.content)
                    if isinstance(content, dict):
                        content['chaos_active'] = True
                        response.content = json.dumps(content)
                        if response.has_header('Content-Length'):
                            del response['Content-Length']
                            
                except (ValueError, TypeError):
                    pass

        return response
