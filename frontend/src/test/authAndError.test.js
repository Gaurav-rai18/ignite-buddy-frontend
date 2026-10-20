import { describe, it, expect, beforeEach } from 'vitest';
import { authService } from '../services/authService';
import { formatErrorMessage } from '../utils/error';

describe('Auth Service', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('rejects empty or invalid email', async () => {
    await expect(authService.login({ email: '', password: 'password123' })).rejects.toThrow(
      'Please enter a valid email address.'
    );
    await expect(authService.login({ email: 'invalid-email', password: 'password123' })).rejects.toThrow(
      'Please enter a valid email address.'
    );
  });

  it('rejects short passwords', async () => {
    await expect(authService.login({ email: 'admin@campus.demo', password: '12' })).rejects.toThrow(
      'Email or password is incorrect.'
    );
  });

  it('successfully logs in and stores in localStorage with rememberMe', async () => {
    const user = await authService.login({
      email: 'admin@campus.demo',
      password: 'password123',
      rememberMe: true,
    });

    expect(user.email).toBe('admin@campus.demo');
    expect(authService.isAuthenticated()).toBe(true);
    expect(authService.getCurrentUser().email).toBe('admin@campus.demo');
  });

  it('successfully logs out and clears authentication', async () => {
    await authService.login({
      email: 'admin@campus.demo',
      password: 'password123',
      rememberMe: true,
    });
    expect(authService.isAuthenticated()).toBe(true);

    authService.logout();
    expect(authService.isAuthenticated()).toBe(false);
    expect(authService.getCurrentUser()).toBeNull();
  });
});

describe('Error Sanitization (formatErrorMessage)', () => {
  it('does NOT render raw HTML error dumps from Django debug pages', () => {
    const htmlError = {
      name: 'ApiError',
      status: 404,
      details: '<!DOCTYPE html><html lang="en"><head><title>Page not found at /api/settings/buddy/</title></head><body><h1>Page not found</h1></body></html>',
    };

    const formatted = formatErrorMessage(htmlError);
    expect(formatted).not.toContain('<!DOCTYPE');
    expect(formatted).not.toContain('<html');
    expect(formatted).toContain('Backend endpoint not found (404)');
  });

  it('formats network failure properly', () => {
    const netErr = new Error('Failed to fetch');
    const formatted = formatErrorMessage(netErr);
    expect(formatted).toContain('Unable to reach the server');
  });

  it('formats standard DRF dictionary errors', () => {
    const drfError = {
      details: {
        title: ['Title is required.'],
        message: ['Ensure this field has at least 5 characters.'],
      },
    };
    const formatted = formatErrorMessage(drfError);
    expect(formatted).toContain('title: Title is required.');
    expect(formatted).toContain('message: Ensure this field has at least 5 characters.');
  });
});
