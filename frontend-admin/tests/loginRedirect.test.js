import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('Login & Default Landing Page Policy Tests', () => {
  it('Login.jsx always navigates directly to /dashboard and does not restore location.state', () => {
    const loginFilePath = resolve('src/pages/Login/Login.jsx');
    const content = readFileSync(loginFilePath, 'utf8');

    // 1. Must navigate to '/dashboard'
    assert.match(
      content,
      /navigate\('\/dashboard',\s*\{\s*replace:\s*true\s*\}\)/,
      'Login.jsx must explicitly navigate to /dashboard with replace: true'
    );

    // 2. Must not read location.state?.from
    assert.doesNotMatch(
      content,
      /location\.state/,
      'Login.jsx must not read location.state to override the landing page'
    );
    assert.doesNotMatch(
      content,
      /from\s*=/,
      'Login.jsx must not declare a variable to route dynamically to previous pages'
    );
  });

  it('ProtectedRoute.jsx redirects to /login cleanly without persisting state.from', () => {
    const protectedRoutePath = resolve('src/components/layout/ProtectedRoute.jsx');
    const content = readFileSync(protectedRoutePath, 'utf8');

    assert.match(
      content,
      /<Navigate to="\/login" replace \/>/,
      'ProtectedRoute must redirect cleanly to /login with replace'
    );
    assert.doesNotMatch(
      content,
      /state=\{\{\s*from:\s*location\s*\}\}/,
      'ProtectedRoute must not store previous location in state'
    );
  });

  it('ErrorBanner component suppresses empty or canceled strings', () => {
    const errorBannerPath = resolve('src/components/ui/ErrorBanner.jsx');
    const content = readFileSync(errorBannerPath, 'utf8');

    assert.match(
      content,
      /message\.trim\(\)\.toLowerCase\(\)\s*===\s*'canceled'/,
      'ErrorBanner must reject canceled messages'
    );
    assert.match(
      content,
      /message\.trim\(\)\.toLowerCase\(\)\s*===\s*'cancelled'/,
      'ErrorBanner must reject cancelled messages'
    );
  });

  it('Login.jsx has removed the Zero Trust Enforced text and badge', () => {
    const loginFilePath = resolve('src/pages/Login/Login.jsx');
    const content = readFileSync(loginFilePath, 'utf8');

    assert.doesNotMatch(
      content,
      /Zero Trust Enforced/,
      'Login.jsx must not display the Zero Trust Enforced text badge'
    );
  });

  it('authService keeps session strictly in memory so browser refresh logs out', () => {
    const authServicePath = resolve('src/services/authService.js');
    const content = readFileSync(authServicePath, 'utf8');

    assert.doesNotMatch(
      content,
      /loadStoredSession/,
      'authService must not restore session from storage on module load'
    );
    assert.doesNotMatch(
      content,
      /sessionStorage\.setItem/,
      'authService must not persist active user into sessionStorage'
    );
  });
});

