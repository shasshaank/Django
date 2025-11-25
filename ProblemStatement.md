# Django: Chaos Engineering Middleware

This challenge involves implementing a custom **Chaos / Resilience Testing Middleware** (similar to Netflix’s Chaos Monkey).  
The goal is to simulate real-world production failures to test downstream client resilience.

By default, the application works normally.  
Your middleware must intercept requests and simulate chaos **only when specific headers are present**.

---

## 🎯 Requirements

### 1. **Admin Immunity**

If the user is a superuser (`request.user.is_superuser == True`), the middleware must:

- Ignore *all* chaos features.
- Bypass delays, failures, mutations.
- Allow the request to continue normally.

---

### 2. **Simulated Latency**

If the request contains:

```
X-Chaos-Delay: <milliseconds>
```

Then the middleware must:

- Pause for the specified duration.
- Convert milliseconds → seconds (e.g. `1500 → 1.5s`)
- Sleep **before** calling the view.

Example:

```
X-Chaos-Delay: 1500
```

Middleware must sleep for **1.5 seconds**.

---

### 3. **Deterministic Failure**

If the request includes:

```
X-Chaos-Mode: 503
```

Then:

1. Compute `len(request.path)`
2. If the length is **even**:
   - Immediately return:

```json
{
  "error": "Chaos Injected"
}
```

   - with status **503 Service Unavailable**
3. If the length is **odd**:
   - Let the request pass normally

Example logic:

- `/abcde` → length 5 → **odd** → allow  
- `/abcdef` → length 6 → **even** → return 503  

---

### 4. **Response Mutation**

If the header is present:

```
X-Chaos-Mutate: True
```

Then, after the view r
