const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  role: 'admin' | 'user';
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  role?: 'admin' | 'user';
}

class AuthAPI {
  private getAuthHeaders(): HeadersInit {
    const token = this.getStoredToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  private setCookie(name: string, value: string, days: number = 7) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
  }

  private getCookie(name: string): string | null {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  }

  private deleteCookie(name: string) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
  }

  async login(data: LoginData): Promise<AuthResponse> {
    try {
      console.log('Attempting login to:', `${API_BASE_URL}/auth/login`);
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      console.log('Login response status:', response.status);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Network error' }));
        console.error('Login error:', error);
        throw new Error(error.detail || 'Login failed');
      }

      const result = await response.json();
      console.log('Login successful:', result.user?.email);
      
      // Store token and user in cookies
      this.setCookie('access_token', result.access_token);
      this.setCookie('user', JSON.stringify(result.user));
      
      return result;
    } catch (error) {
      console.error('Login request failed:', error);
      throw error;
    }
  }

  async signup(data: SignupData): Promise<AuthResponse> {
    try {
      console.log('Attempting signup to:', `${API_BASE_URL}/auth/signup`);
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      console.log('Signup response status:', response.status);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Network error' }));
        console.error('Signup error:', error);
        throw new Error(error.detail || 'Signup failed');
      }

      const result = await response.json();
      console.log('Signup successful:', result.user?.email);
      
      // Store token and user in cookies
      this.setCookie('access_token', result.access_token);
      this.setCookie('user', JSON.stringify(result.user));
      
      return result;
    } catch (error) {
      console.error('Signup request failed:', error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user info');
    }

    return response.json();
  }

  async logout(): Promise<void> {
    this.deleteCookie('access_token');
    this.deleteCookie('user');
  }

  getStoredUser(): User | null {
    const userStr = this.getCookie('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  }

  getStoredToken(): string | null {
    return this.getCookie('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.getStoredToken();
  }

  isAdmin(): boolean {
    const user = this.getStoredUser();
    return user?.role === 'admin';
  }
}

export const authAPI = new AuthAPI();
