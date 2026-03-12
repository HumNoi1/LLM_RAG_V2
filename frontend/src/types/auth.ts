import { UserRole, UUID, ISODate } from './common';

// Auth Request/Response types
export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface UserResponse {
  id: UUID;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: ISODate;
}
