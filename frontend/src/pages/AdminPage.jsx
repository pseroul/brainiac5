import React, { useState, useEffect, useCallback } from 'react';
import { Shield, UserPlus, Pencil, Trash2, X, Check, Copy, RefreshCw } from 'lucide-react';
import {
  getAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
} from '../services/api';
import { useAuth } from '../contexts/AuthContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const EMPTY_FORM = { username: '', email: '', is_admin: false };

function Badge({ isAdmin }) {
  return isAdmin ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
      <Shield size={11} /> Admin
    </span>
  ) : (
    <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs">User</span>
  );
}

// ---------------------------------------------------------------------------
// OTP URI display modal
// ---------------------------------------------------------------------------

function OtpModal({ otpUri, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(otpUri).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="otp-modal">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-gray-900">User created</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>
        <p className="text-sm text-gray-600 mb-3">
          Share the following TOTP provisioning URI with the new user so they can set up their
          authenticator app (e.g. Google Authenticator).
        </p>
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 text-xs font-mono break-all text-gray-700">
          {otpUri}
        </div>
        <div className="flex gap-2 mt-4">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy URI'}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// User form modal (create / edit)
// ---------------------------------------------------------------------------

function UserFormModal({ initial, onSubmit, onClose, isLoading }) {
  const [form, setForm] = useState(initial ?? EMPTY_FORM);
  const [error, setError] = useState('');
  const isEdit = !!initial;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    if (error) setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.username.trim()) { setError('Username is required'); return; }
    if (!form.email.trim())    { setError('Email is required'); return; }
    onSubmit(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="user-form-modal">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-gray-900">
            {isEdit ? 'Edit user' : 'Create user'}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-3 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={form.username}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              required
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_admin"
              name="is_admin"
              type="checkbox"
              checked={form.is_admin}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label className="text-sm font-medium text-gray-700" htmlFor="is_admin">
              Admin privileges
            </label>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <Check size={16} />}
              {isEdit ? 'Save changes' : 'Create user'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AdminPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [pageError, setPageError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null);      // user object to edit
  const [deleteTarget, setDeleteTarget] = useState(null);  // user id to delete
  const [otpUri, setOtpUri] = useState('');

  const loadUsers = useCallback(async () => {
    try {
      const res = await getAdminUsers();
      setUsers(res.data);
      setPageError('');
    } catch {
      setPageError('Failed to load users.');
    }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  // CREATE
  const handleCreate = async (form) => {
    setIsLoading(true);
    try {
      const res = await createAdminUser(form);
      setOtpUri(res.data.otp_uri);
      setShowCreateModal(false);
      loadUsers();
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Failed to create user.';
      setPageError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  // UPDATE
  const handleUpdate = async (form) => {
    setIsLoading(true);
    try {
      await updateAdminUser(editTarget.id, form);
      setEditTarget(null);
      loadUsers();
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Failed to update user.';
      setPageError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  // DELETE
  const handleDelete = async () => {
    if (deleteTarget === null) return;
    setIsLoading(true);
    try {
      await deleteAdminUser(deleteTarget);
      setDeleteTarget(null);
      loadUsers();
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Failed to delete user.';
      setPageError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Shield className="text-blue-600" size={28} />
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
        >
          <UserPlus size={18} /> Add user
        </button>
      </div>

      {/* Error banner */}
      {pageError && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm flex items-center justify-between">
          {pageError}
          <button onClick={() => setPageError('')}><X size={16} /></button>
        </div>
      )}

      {/* User table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-gray-500 font-medium">ID</th>
              <th className="px-4 py-3 text-left text-gray-500 font-medium">Username</th>
              <th className="px-4 py-3 text-left text-gray-500 font-medium">Email</th>
              <th className="px-4 py-3 text-left text-gray-500 font-medium">Role</th>
              <th className="px-4 py-3 text-right text-gray-500 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{u.id}</td>
                <td className="px-4 py-3 font-medium text-gray-900">{u.username}</td>
                <td className="px-4 py-3 text-gray-600">{u.email}</td>
                <td className="px-4 py-3"><Badge isAdmin={!!u.is_admin} /></td>
                <td className="px-4 py-3 text-right flex justify-end gap-1">
                  <button
                    onClick={() => setEditTarget(u)}
                    className="p-2 rounded-lg hover:bg-blue-50 text-blue-600 transition-colors"
                    title="Edit"
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    onClick={() => setDeleteTarget(u.id)}
                    disabled={u.email === user?.email}
                    className="p-2 rounded-lg hover:bg-red-50 text-red-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title={u.email === user?.email ? 'Cannot delete yourself' : 'Delete'}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Delete confirmation */}
      {deleteTarget !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="delete-confirm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Delete user?</h2>
            <p className="text-sm text-gray-600 mb-4">This action cannot be undone.</p>
            <div className="flex gap-2">
              <button
                onClick={handleDelete}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <Trash2 size={16} />}
                Delete
              </button>
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create modal */}
      {showCreateModal && (
        <UserFormModal
          onSubmit={handleCreate}
          onClose={() => setShowCreateModal(false)}
          isLoading={isLoading}
        />
      )}

      {/* Edit modal */}
      {editTarget && (
        <UserFormModal
          initial={editTarget}
          onSubmit={handleUpdate}
          onClose={() => setEditTarget(null)}
          isLoading={isLoading}
        />
      )}

      {/* OTP URI modal (shown after creation) */}
      {otpUri && (
        <OtpModal otpUri={otpUri} onClose={() => setOtpUri('')} />
      )}
    </div>
  );
}
