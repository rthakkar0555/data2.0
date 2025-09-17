# Authentication System Setup

## Overview
This project now includes a complete authentication system with role-based access control.

## Features
- **Login/Signup**: Users can create accounts and login
- **Role-based Access**: Admin and User roles with different permissions
- **JWT Authentication**: Secure token-based authentication
- **MongoDB Storage**: User data stored in MongoDB
- **Route Protection**: Middleware protects routes based on authentication and roles

## Default Admin Account
- **Email**: admin@manualbase.com
- **Password**: admin123
- **Role**: admin

## Setup Instructions

### 1. Backend Setup
1. Install the new dependencies:
   ```bash
   cd Rag_Manual_retrival/backend
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```bash
   python main.py
   ```

### 2. Frontend Setup
1. Create a `.env.local` file in the root directory:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Start the frontend:
   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication Endpoints
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info
- `GET /auth/admin-only` - Admin-only endpoint

### Request/Response Examples

#### Signup
```json
POST /auth/signup
{
  "email": "user@example.com",
  "password": "password123",
  "role": "user"
}
```

#### Login
```json
POST /auth/login
{
  "email": "admin@manualbase.com",
  "password": "admin123"
}
```

#### Response
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## User Roles

### Admin Role
- Access to `/admin` panel
- Can access all admin-only endpoints
- Full system access

### User Role
- Access to `/user` panel only
- Cannot access admin endpoints
- Limited system access

## Security Features
- Passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes
- Tokens stored in HTTP-only cookies
- Role-based route protection
- CSRF protection through middleware

## File Structure
```
├── Rag_Manual_retrival/backend/
│   ├── auth.py              # Authentication endpoints
│   ├── main.py              # Main FastAPI app
│   └── requirements.txt     # Updated dependencies
├── lib/
│   └── auth-api.ts          # Frontend API client
├── contexts/
│   └── AuthContext.tsx      # React context for auth state
├── components/
│   └── logout-button.tsx    # Logout component
├── middleware.ts             # Route protection middleware
└── app/login/page.tsx       # Updated login page
```

## Usage

### For Users
1. Go to `/login`
2. Click "Don't have an account? Sign Up"
3. Create account with email and password
4. Automatically redirected to `/user` panel

### For Admins
1. Go to `/login`
2. Login with admin credentials:
   - Email: admin@manualbase.com
   - Password: admin123
3. Automatically redirected to `/admin` panel

### Adding Logout
Include the LogoutButton component in your admin/user panels:
```tsx
import { LogoutButton } from "@/components/logout-button"

// In your component
<LogoutButton />
```

## Troubleshooting

### Common Issues
1. **CORS Errors**: Make sure backend is running on port 8000
2. **Authentication Failed**: Check if MongoDB is connected
3. **Token Expired**: Tokens expire after 30 minutes, user needs to login again

### MongoDB Connection
The system uses the existing MongoDB connection from `main.py`. Make sure your MongoDB URI is correct in the environment variables.

## Production Considerations
1. Change the SECRET_KEY in `auth.py`
2. Set secure cookie flags in production
3. Use HTTPS in production
4. Implement token refresh mechanism
5. Add rate limiting for login attempts
