#Frontend
1. cd frontend
2. npm run dev

# Backend
1. cd backend
2. python manage.py runserver

September 11 2025
1) Goal
 - We want the frontend to say “Hi [username]” without manually storing what the user typed. The best source of truth is the login token the server issues.
2) Why change backend/api/views.py
- The default SimpleJWT token doesn’t include the username, just things like user id and expiry.
- So we created a custom “token maker”:
 - A custom serializer that adds username into the token payload when the token is created.
 - A custom view that uses that serializer.
- Net effect: every time someone logs in, the token now contains username inside it.
3) Why change backend/backend/urls.py
- Your login URL /api/token/ originally pointed to the default token view (which doesn’t add username).
- We switched that URL to point to our custom token view.
- Net effect: from now on, when the frontend requests a token at /api/token/, it gets the enhanced token with username.
4) What happens at login now
- User enters username/password.
- Frontend calls /api/token/.
- That hits your custom token view, which issues a token that includes username.
- Frontend decodes that token and reads the username to show “Hi [username]”.
- If there’s no valid token (e.g., logged out), the UI falls back to “Hi there”.