/**
 * User Identity & Initials Helpers for Ignite Buddy Admin Console.
 * Generates dynamic names, 2-letter uppercase initials, and role badges
 * from authenticated user models (no hardcoded "Admin" or "ADMIN").
 */

export function getUserDisplayName(user) {
  if (!user) return 'User';
  
  if (user.full_name && user.full_name.trim()) {
    return user.full_name.trim();
  }

  const first = (user.first_name || '').trim();
  const last = (user.last_name || '').trim();
  if (first || last) {
    return `${first} ${last}`.trim();
  }

  if (user.username && user.username.trim()) {
    return user.username.trim();
  }

  if (user.email) {
    const local = user.email.split('@')[0];
    return local.charAt(0).toUpperCase() + local.slice(1);
  }

  return 'User';
}

export function getUserInitials(user) {
  if (!user) return 'U';

  // If user has a name
  const displayName = getUserDisplayName(user);
  if (displayName && displayName !== 'User') {
    const parts = displayName.split(/[\s._-]+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    if (parts.length === 1 && parts[0].length >= 2) {
      return parts[0].slice(0, 2).toUpperCase();
    }
    if (parts.length === 1) {
      return parts[0][0].toUpperCase();
    }
  }

  if (user.email) {
    const local = user.email.split('@')[0];
    const letters = local.replace(/[^a-zA-Z]/g, '');
    if (letters.length >= 2) {
      return letters.slice(0, 2).toUpperCase();
    }
    if (letters.length === 1) {
      return letters[0].toUpperCase();
    }
    return local.slice(0, 2).toUpperCase();
  }

  return 'U';
}

export function getUserRoleLabel(role, isSuperuser = false) {
  if (isSuperuser) return 'Workspace Owner';

  const normalized = (role || '').toUpperCase();
  switch (normalized) {
    case 'ADMIN':
      return 'Ignite Administrator';
    case 'TA':
      return 'Faculty / TA';
    case 'MANAGER':
      return 'Ignite Manager';
    case 'HR':
      return 'Human Resources';
    case 'TRAINEE':
      return 'Student Trainee';
    default:
      return role || 'Member';
  }
}

