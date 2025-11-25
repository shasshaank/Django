Test Cases
The following test suite verifies that the ChaosMiddleware correctly implements the four core requirements: Admin Immunity, Latency, Deterministic Failure, and Response Mutation.

Python Test Suite (tests.py)



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
        # Create a request that WOULD fail for a normal user (Even path + Chaos Mode)
        request = self.factory.get('/evenpath', headers={'X-Chaos-Mode': '503'})
        
        # Create and attach a mock superuser
        request.user = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        
        response = self.middleware(request)
        
        # Expectation: 200 OK (Bypassed the 503 error)
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
        
        # Expectation: Duration is at least 0.5s (allowing for small execution overhead)
        self.assertGreaterEqual(duration, 0.5)
        # Sanity check: shouldn't be erroneously long (e.g., > 2s)
        self.assertLess(duration, 2.0)

    def test_deterministic_failure_even_path(self):
        """
        Requirement 3a: Deterministic Failure (Even Path)
        If 'X-Chaos-Mode: 503' is set AND path length is EVEN -> Return 503.
        """
        # '/123456' is length 7 (odd). '/12345' is length 6 (even).
        
        # Path: /12345 (Length 6 -> Even)
        request = self.factory.get('/12345', headers={'X-Chaos-Mode': '503'})
        request.user = AnonymousUser()
        
        response = self.middleware(request)
        
        # Expectation: 503 Service Unavailable
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content)['error'], "Chaos Injected")

    def test_deterministic_failure_odd_path(self):
        """
        Requirement 3b: Deterministic Failure (Odd Path)
        If 'X-Chaos-Mode: 503' is set AND path length is ODD -> Pass through.
        """
        # Path: /1234 (Length 5 -> Odd)
        request = self.factory.get('/1234', headers={'X-Chaos-Mode': '503'})
        request.user = AnonymousUser()
        
        response = self.middleware(request)
        
        # Expectation: 200 OK (Normal processing)
        self.assertEqual(response.status_code, 200)

    def test_response_mutation(self):
        """
        Requirement 4: Response Mutation
        If 'X-Chaos-Mutate: True' is set, inject "chaos_active": true into the JSON response.
        """
        request = self.factory.get('/', headers={'X-Chaos-Mutate': 'True'})
        request.user = AnonymousUser()
        
        response = self.middleware(request)
        
        # Expectation: 200 OK
        self.assertEqual(response.status_code, 200)
        
        content = json.loads(response.content)
        
        # Verify original data remains
        self.assertEqual(content['status'], 'ok')
        # Verify injected key
        self.assertTrue(content.get('chaos_active'), "Response should contain 'chaos_active': True")
