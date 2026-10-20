const STORAGE_KEY = 'tcs_admin_users_demo';

const INITIAL_USERS = [
  {
    id: 'user-1',
    name: 'Arun Kumar',
    email: 'arun.kumar@campus.demo',
    role: 'Student',
    department: 'Information Technology',
    status: 'Active',
    initials: 'AK',
  },
  {
    id: 'user-2',
    name: 'Priya S',
    email: 'priya.s@campus.demo',
    role: 'Student',
    department: 'Computer Science',
    status: 'Active',
    initials: 'PS',
  },
  {
    id: 'user-3',
    name: 'Karthik R',
    email: 'karthik.r@campus.demo',
    role: 'Admin',
    department: 'Administration',
    status: 'Active',
    initials: 'KR',
  },
  {
    id: 'user-4',
    name: 'Divya M',
    email: 'divya.m@campus.demo',
    role: 'Student',
    department: 'Information Technology',
    status: 'Inactive',
    initials: 'DM',
  },
];

function getStoredUsers() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_USERS));
      return INITIAL_USERS;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : INITIAL_USERS;
  } catch {
    return INITIAL_USERS;
  }
}

function saveStoredUsers(users) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
  } catch {
    // Storage quota or private mode fallback
  }
}

function makeInitials(name = '') {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return (name.slice(0, 2) || 'US').toUpperCase();
}

export const usersService = {
  getUsers: async () => {
    // Simulated network delay for realistic enterprise feel
    await new Promise((resolve) => setTimeout(resolve, 80));
    return getStoredUsers();
  },

  createUser: async (userData) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredUsers();
    const newUser = {
      id: `user-${Date.now()}`,
      name: userData.name.trim(),
      email: userData.email.trim(),
      role: userData.role || 'Student',
      department: userData.department.trim() || 'General',
      status: userData.status || 'Active',
      initials: makeInitials(userData.name),
      created_at: new Date().toISOString(),
    };
    const updated = [newUser, ...current];
    saveStoredUsers(updated);
    return newUser;
  },

  updateUser: async (userId, userData) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredUsers();
    const index = current.findIndex((u) => u.id === userId);
    if (index === -1) {
      throw new Error('User not found.');
    }
    const updatedUser = {
      ...current[index],
      name: userData.name.trim(),
      email: userData.email.trim(),
      role: userData.role || current[index].role,
      department: userData.department.trim() || current[index].department,
      status: userData.status || current[index].status,
      initials: makeInitials(userData.name),
      updated_at: new Date().toISOString(),
    };
    current[index] = updatedUser;
    saveStoredUsers(current);
    return updatedUser;
  },

  deleteUser: async (userId) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredUsers();
    const filtered = current.filter((u) => u.id !== userId);
    saveStoredUsers(filtered);
    return { success: true, id: userId };
  },
};
