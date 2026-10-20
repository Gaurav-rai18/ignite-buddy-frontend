import React, { useState } from 'react';
import { Users, UserPlus, Search, RotateCw, ShieldAlert } from 'lucide-react';
import { useUsers } from '../../hooks/useUsers';
import { UserTable } from '../../components/users/UserTable';
import { UserFormModal } from '../../components/users/UserFormModal';
import { DeleteUserDialog } from '../../components/users/DeleteUserDialog';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export function ManageUsers({ onNotify }) {
  const {
    users,
    filteredUsers,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    addUser,
    editUser,
    deleteUser,
    refetch,
  } = useUsers();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [deletingUser, setDeletingUser] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
    if (onNotify) {
      onNotify('User roles and details refreshed');
    }
  };

  const handleOpenAdd = () => {
    setEditingUser(null);
    setIsFormOpen(true);
  };

  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (formData) => {
    if (editingUser) {
      await editUser(editingUser.id, formData);
      if (onNotify) {
        onNotify(`User ${formData.name} updated successfully`);
      }
    } else {
      await addUser(formData);
      if (onNotify) {
        onNotify(`User ${formData.name} added successfully`);
      }
    }
  };

  const handleDeleteConfirm = async (userId) => {
    await deleteUser(userId);
    if (onNotify) {
      onNotify('User deleted successfully');
    }
  };

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" aria-hidden="true" />
            ACCESS & PERMISSIONS
          </div>
          <h1>Manage Users</h1>
          <p className="subheading">Create, edit, and organise user roles.</p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={handleRefresh}
          disabled={loading || isRefreshing}
        >
          <RotateCw
            size={14}
            style={{
              animation: loading || isRefreshing ? 'spin 1s linear infinite' : 'none',
            }}
            aria-hidden="true"
          />
          {loading || isRefreshing ? 'Refreshing...' : 'Refresh data'}
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <section className="panel" style={{ padding: '24px' }}>
        <div className="panel-heading" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="stat-icon primary" style={{ width: '40px', height: '40px' }} aria-hidden="true">
              <Users size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', marginBottom: '2px' }}>Manage users</h3>
              <p>Add users, update details, and assign demo roles</p>
            </div>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={handleOpenAdd}
          >
            <UserPlus size={16} aria-hidden="true" />
            Add user
          </button>
        </div>

        <div className="table-search-bar">
          <div className="search-input-wrap">
            <Search size={16} aria-hidden="true" />
            <input
              type="text"
              placeholder="Search users, email or role.."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search users by name, email, or role"
            />
          </div>
          <span className="search-count-badge">
            {filteredUsers.length} users
          </span>
        </div>

        <UserTable
          users={filteredUsers}
          onEdit={handleOpenEdit}
          onDelete={(u) => setDeletingUser(u)}
        />

        <div className="card-table-footer">
          <span>
            Showing {filteredUsers.length} of {users.length} users
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <ShieldAlert size={13} color="var(--color-primary)" aria-hidden="true" />
            Role assignment is demo-only
          </span>
        </div>
      </section>

      <UserFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        initialUser={editingUser}
      />

      <DeleteUserDialog
        isOpen={Boolean(deletingUser)}
        user={deletingUser}
        onClose={() => setDeletingUser(null)}
        onConfirm={handleDeleteConfirm}
      />
    </>
  );
}
