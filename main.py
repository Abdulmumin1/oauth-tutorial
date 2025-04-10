from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Annotated
from fastapi import Query
import requests
import jwt
from jwt import PyJWTError
import datetime

app = FastAPI()


GOOGLE_CLIENT_ID = '338812318712-uuklfk7f0mmd39fihe2b6m5c6s4e86db.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

REDIRECT_URI = 'http://localhost:8000/auth/redirect/google'
SECRET_KEY = "your-super-secret"
EXCLUDE_PATHS = ['/dashboard', '/', '/auth/redirect/google']
EXCLUDE_PREFIXES = []
ALGORITHM = "HS256"

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in EXCLUDE_PATHS or any(path.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                print(token)
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                request.state.user = payload
            except PyJWTError:
                return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)
        else:
            return JSONResponse({"detail": "Authorization header missing"}, status_code=401)

        return await call_next(request)


app.add_middleware(JWTMiddleware)
@app.get('/', response_class=HTMLResponse)
def redirect_to_auth():
    URL =  f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=email%20profile&access_type=offline"
    return  """
        <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Sign In</title>
    <style>
        * {
        box-sizing: border-box;
        }

        body, html {
        margin: 0;
        padding: 0;
        min-height: 100vh;
        font-family: sans-serif;
        background-color: #f9fafb; /* bg-gray-50 */
        display: flex;
        align-items: center;
        justify-content: center;
        }

        .container {
        max-width: 28rem; /* max-w-md */
        width: 100%;
        padding: 1.5rem; /* p-6 */
        background-color: #fff;
        border-radius: 0.5rem; /* rounded-lg */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* shadow-md */
        }

        h1 {
        font-size: 1.5rem; /* text-2xl */
        font-weight: bold;
        text-align: center;
        margin-bottom: 1.5rem; /* mb-6 */
        }

        .google-button {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        background-color: #fff;
        border: 1px solid #d1d5db; /* border-gray-300 */
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem; /* px-6 py-2 */
        font-size: 0.875rem; /* text-sm */
        font-weight: 500;
        color: #1f2937; /* text-gray-800 */
        cursor: pointer;
        transition: background-color 0.2s;
        }

        .google-button:hover {
        background-color: #f9fafb; /* hover:bg-gray-50 */
        }

        .google-button:focus {
        outline: 2px solid transparent;
        outline-offset: 2px;
        box-shadow: 0 0 0 2px #6b7280; /* focus:ring-gray-500 */
        }

        .google-logo {
        width: 1.25rem; /* w-5 */
        height: 1.25rem; /* h-5 */
        }
    </style>
    </head>
    <body>
    <main class="container" >
        <div id="signin-container">
        <h1>Sign In</h1>
        <button class="google-button" onclick="signInWithGoogle()"
        >
        <img
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
            alt="Google logo"
            class="google-logo"
        />
        Sign in with Google
        </button>
        </div>
    </main>

    

    <script>
        function signInWithGoogle() {
            window.location.href = {{AUTH_URL}}
        }

         (function () {

      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token') || localStorage.getItem('auth_token');

      if (token) {
        localStorage.setItem('auth_token', token);
        // Optional: Redirect to a dashboard or another page
        window.location.href = "/dashboard"; 
      } else {
        document.getElementById('signin-container').style.display = 'block';
      }
    })();
    </script>
    </body>
    </html>
    """.replace("{{AUTH_URL}}", f"'{URL}'")
    
@app.get('/dashboard', response_class=HTMLResponse)
def dashboard():
    return """
            <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Dashboard</title>
        <style>
            body, html {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            background-color: #f0f4f8;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            }

            .dashboard {
            background-color: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            width: 100%;
            text-align: center;
            }

            .dashboard h1 {
            margin-bottom: 1rem;
            }

            .user-info {
            font-size: 1rem;
            color: #333;
            }

            .signout {
            margin-top: 1.5rem;
            background: #ef4444;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            }
        </style>
        </head>
        <body>
        <div class="dashboard" id="dashboard">
            <h1>Welcome</h1>
            <div class="user-info" id="user-info">Loading...</div>
            <button class="signout" onclick="signOut()">Sign Out</button>
        </div>

        <script>
            async function loadUser() {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                window.location.href = '/'; // redirect to sign-in
                return;
            }

            try {
                const res = await fetch('http://localhost:8000/user/details', {
               
                headers: {
                    'Authorization': `Bearer ${token}`
                }
                });
                if (!res.ok) {
                throw new Error('Invalid token');
                }

                const user = await res.json();
                console.log(user?.user)
                document.getElementById('user-info').textContent = `Hello, ${user.user.info.name} (${user.user.info.email})`;
            } catch (err) {
                console.error(err);
            }
            }

            function signOut() {
            localStorage.removeItem('auth_token');
            window.location.href = '/';
            }

            loadUser();
        </script>
        </body>
        </html>
    
    """


@app.get('/auth/redirect/google')
def authenticate(code: Annotated[str, Query(code="code")]):

    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    credentials_response = requests.post(url, data=data, headers=headers)

    credentials = credentials_response.json()
    # return credentials
    access_token = credentials['access_token']

    user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'

    headers = {
         'Authorization': f"Bearer {access_token}"
    }

    user_info_response = requests.get(user_info_url, headers=headers)

    user_info = user_info_response.json();

    user_id  = user_info['id']

    payload = {
    "sub": user_id, 
    'info': user_info,
    "iat": datetime.datetime.utcnow(),  # issued at
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # expires in 1 hour
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return RedirectResponse(url=f"http://localhost:8000?token={token}")

@app.get('/user/details')
def get_user_details(request: Request):
    user = getattr(request.state, "user", None)
    return {"user":user}