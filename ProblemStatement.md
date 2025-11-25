# Django: Chaos Engineering Middleware

In this challenge, your task is to implement a custom Resilience Testing Middleware (often referred to as a "Chaos Monkey"). The goal is to intentionally simulate production failures (latency, errors, data mutation) to ensure that downstream clients can handle instability gracefully.

The provided application functions normally by default. Your middleware must intercept requests and "break" them according to specific headers provided in the request.

The custom Middleware must process requests and act according to the following requirements:

## 1. Admin Immunity

If the user making the request is a superuser (request.user.is_superuser), the middleware must ignore all chaos rules and allow the request to proceed normally, regardless of any headers.

## 2. Simulated Latency

If the request contains the header `X-Chaos-Delay`, the middleware must pause execution for the number of milliseconds specified in the header value before processing the view.

Example: `X-Chaos-Delay: 1500` should pause for 1.5 seconds.

## 3. Deterministic Failure

If the header `X-Chaos-Mode: 503` is present, the middleware must inspect the length of the request path (e.g., `/api/data/`).

If the path length is an even number, immediately return a `JsonResponse` with status 503 (Service Unavailable) and body:

```json
{"error": "Chaos Injected"}
```

If the path length is odd, allow the request to proceed.

## 4. Response Mutation

If the header `X-Chaos-Mutate: True` is present, the middleware must intercept the final response. If the response is a JSON response, it must inject a new key-value pair `{"chaos_active": true}` into the JSON body before sending it to the client.

Implementations for the basic views are provided. In order to define your custom Middleware according to the above requirements, you will need to define it in a new file (e.g., `project/middleware.py`) and point to this implementation in the `MIDDLEWARE` list in `project/settings.py`.
