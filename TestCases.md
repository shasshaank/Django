# ChaosMiddleware Test Suite

This test suite verifies that the `ChaosMiddleware` correctly implements the four core requirements:

1. **Admin Immunity**  
2. **Simulated Latency**  
3. **Deterministic Failure**  
4. **Response Mutation**

## `tests.py`

```python
# --- Mock View ---

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.http import JsonResponse
import json
import time
from project.middleware import ChaosMiddleware

def mock_view_success(request):
    """
    A simple mock view that returns a standard JSON response.
    Used to verify that the middleware passes requests through correctly.
    """
    return JsonResponse({"status": "ok", "data": [1, 2, 3]})

class ChaosMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ChaosMiddleware(mock_view_success)

    def test_admin_immunity(self):
        """
        Requirement 1: Admin Immunity
        Superusers should bypass ALL chaos logic (latency, errors, etc.),
        even if chaos headers are present.
        """
        request = self.factory.get('/evenpath', headers={'X-Chaos-Mode': '503'})
        request.user = User.objects.create_superuser('admin', 'admin@test.com', 'pass')

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_simulated_latency(self):
        """
        Requirement 2: Simulated Latency
        If 'X-Chaos-Delay' is present, the middleware should sleep for X ms.
        """
        delay_ms = 500
        request = self.factory.get('/', headers={'X-Chaos-Delay': str(delay_ms)})
        request.user = AnonymousUser()

        start_time = time.time()
        self.middleware(request)
        end_time = time.time()

        duration = end_time - start_time
        self.assertGreaterEqual(duration, 0.5)
        self.assertLess(duration, 2.0)

    def test_deterministic_failure_even_path(self):
        """
        Requirement 3a: Deterministic Failure (Even Path)
        If 'X-Chaos-Mode: 503' is set AND path length is EVEN -> Return 503.
        """
        request = self.factory.get('/12345', headers={'X-Chaos-Mode': '503'})  # even length
        request.user = AnonymousUser()

        response = self.middleware(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content)['error'], "Chaos Injected")

    def test_deterministic_failure_odd_path(self):
        """
        Requirement 3b: Deterministic Failure (Odd Path)
        If 'X-Chaos-Mode: 503' is set AND path length is ODD -> Pass through.
        """
        request = self.factory.get('/1234', headers={'X-Chaos-Mode': '503'})  # odd length
        request.user = AnonymousUser()

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_response_mutation(self):
        """
        Requirement 4: Response Mutation
        If 'X-Chaos-Mutate: True' is set, inject "chaos_active": true into the JSON response.
        """
        request = self.factory.get('/', headers={'X-Chaos-Mutate': 'True'})
        request.user = AnonymousUser()

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        self.assertEqual(content['status'], 'ok')
        self.assertTrue(content.get('chaos_active'))
```
