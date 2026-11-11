import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Search,
  RotateCw,
  ShieldAlert,
  Layers,
} from 'lucide-react';

import { useUsers } from '../../hooks/useUsers';
import { UserTable } from '../../components/users/UserTable';
import { UserFormModal } from '../../components/users/UserFormModal';
import { DeleteUserDialog } from '../../components/users/DeleteUserDialog';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BulkUploadUserModal } from '../../components/users/BulkUploadUserModal';
import { BatchHierarchyModal } from '../../components/users/BatchHierarchyModal';
import { usersService } from '../../services/usersService';

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
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [hierarchyModalOpen, setHierarchyModalOpen] = useState(false);

  // ============================
  // Pagination
  // ============================

  const USERS_PER_PAGE = 15;

  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(
    filteredUsers.length / USERS_PER_PAGE
  );

  const startIndex =
    (currentPage - 1) * USERS_PER_PAGE;

  const endIndex =
    startIndex + USERS_PER_PAGE;

  const paginatedUsers =
    filteredUsers.slice(
      startIndex,
      endIndex
    );

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

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

  const handleFormSubmit = async (formData, maybeId) => {
    const targetId = maybeId || editingUser?.id || editingUser?.pk;
    if (targetId) {
      await editUser(targetId, formData);

      if (onNotify) {
        onNotify(
          `User ${formData.username || 'details'} updated successfully`
        );
      }
    } else {
      await addUser(formData);

      if (onNotify) {
        onNotify(
          `User ${formData.username} added successfully`
        );
      }
    }
  };

  const handleDeleteConfirm = async (
    userId
  ) => {
    await deleteUser(userId);

    if (onNotify) {
      onNotify(
        'User deleted successfully'
      );
    }
  };

  const handleBulkUpload = async (
    file
  ) => {
    try {
      const result =
        await usersService.bulkUploadUsers(
          file
        );

      await refetch();

      if (onNotify) {
        onNotify(
          `${result.created_count} users added successfully. ${result.failed_count} users could not be added.`
        );
      }

      console.log(result);
    } catch (error) {
      console.error(error);

      if (onNotify) {
        onNotify('Bulk upload failed');
      }
    }
  };

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span
              className="eyebrow-line"
              aria-hidden="true"
            />
            ACCESS & PERMISSIONS
          </div>

          <h1>Manage Users</h1>

          <p className="subheading">
            Create, edit and organise user
            roles.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={handleRefresh}
          disabled={
            loading || isRefreshing
          }
        >
          <RotateCw
            size={14}
            style={{
              animation:
                loading || isRefreshing
                  ? 'spin 1s linear infinite'
                  : 'none',
            }}
            aria-hidden="true"
          />

          {loading || isRefreshing
            ? 'Refreshing...'
            : 'Refresh data'}
        </button>
      </div>

      {error && (
        <ErrorBanner
          message={error}
          onRetry={refetch}
        />
      )}

      <section
        className="panel"
        style={{ padding: '24px' }}
      >
        <div
          className="panel-heading"
          style={{
            marginBottom: '20px',
            display: 'flex',
            justifyContent:
              'space-between',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <div
              className="stat-icon primary"
              style={{
                width: '40px',
                height: '40px',
              }}
              aria-hidden="true"
            >
              <Users size={20} />
            </div>

            <div>
              <h3
                style={{
                  fontSize: '15px',
                  marginBottom: '2px',
                }}
              >
                Manage users
              </h3>

              <p>
                Add users, update
                details, and assign
                demo roles
              </p>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <button
              type="button"
              className="secondary-button"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              onClick={() => setHierarchyModalOpen(true)}
            >
              <Layers size={16} aria-hidden="true" />
              Manage Batches & Cohorts
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={() =>
                setBulkModalOpen(true)
              }
            >
              Bulk Upload
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={handleOpenAdd}
            >
              <UserPlus
                size={16}
                aria-hidden="true"
              />
              Add User
            </button>
          </div>
        </div>

        <div className="table-search-bar">
          <div className="search-input-wrap">
            <Search
              size={16}
              aria-hidden="true"
            />

            <input
              type="text"
              placeholder="Search users, email or role.."
              value={searchQuery}
              onChange={(e) =>
                setSearchQuery(
                  e.target.value
                )
              }
              aria-label="Search users by name, email, or role"
            />
          </div>

          <span className="search-count-badge">
            {filteredUsers.length} users
          </span>
        </div>

        <UserTable
          users={paginatedUsers}
          onEdit={handleOpenEdit}
          onDelete={(u) =>
            setDeletingUser(u)
          }
        />

        {/* Pagination */}
        {filteredUsers.length > 50 && (
          <div
            style={{
              display: 'flex',
              justifyContent:
                'space-between',
              alignItems: 'center',
              marginTop: '20px',
              padding: '10px 0',
            }}
          >
            <button
              type="button"
              className="secondary-button"
              disabled={
                currentPage === 1
              }
              onClick={() =>
                setCurrentPage(
                  (prev) =>
                    Math.max(
                      prev - 1,
                      1
                    )
                )
              }
            >
              Previous
            </button>

            <span
              style={{
                fontWeight: 600,
              }}
            >
              Page {currentPage} of{' '}
              {totalPages}
            </span>

            <button
              type="button"
              className="secondary-button"
              disabled={
                currentPage ===
                totalPages
              }
              onClick={() =>
                setCurrentPage(
                  (prev) =>
                    Math.min(
                      prev + 1,
                      totalPages
                    )
                )
              }
            >
              Next
            </button>
          </div>
        )}

        <div className="card-table-footer">
          <span>
            Showing{' '}
            {filteredUsers.length === 0
              ? 0
              : startIndex + 1}
            -
            {Math.min(
              endIndex,
              filteredUsers.length
            )}{' '}
            of {filteredUsers.length}{' '}
            users
          </span>

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <ShieldAlert
              size={13}
              color="var(--color-primary)"
              aria-hidden="true"
            />
            Role assignment is
            demo-only
          </span>
        </div>
      </section>

      <UserFormModal
        isOpen={isFormOpen}
        onClose={() =>
          setIsFormOpen(false)
        }
        onSubmit={handleFormSubmit}
        initialUser={editingUser}
      />

      <DeleteUserDialog
        isOpen={Boolean(deletingUser)}
        user={deletingUser}
        onClose={() =>
          setDeletingUser(null)
        }
        onConfirm={
          handleDeleteConfirm
        }
      />

      <BulkUploadUserModal
        isOpen={bulkModalOpen}
        onClose={() =>
          setBulkModalOpen(false)
        }
        onUpload={
          handleBulkUpload
        }
      />

      <BatchHierarchyModal
        isOpen={hierarchyModalOpen}
        onClose={() => setHierarchyModalOpen(false)}
        onHierarchyUpdated={() => {
          refetch();
          if (onNotify) {
            onNotify('Batch hierarchy updated successfully');
          }
        }}
      />
    </>
  );
}
