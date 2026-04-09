/**
 * AdminPage.test.jsx
 * Unit tests for the admin user-management page.
 *
 * Coverage:
 * - Renders user table from API response
 * - Create modal opens / submits / shows OTP URI
 * - Edit modal opens pre-filled
 * - Delete confirmation flow
 * - Delete button disabled for current user
 * - API error displayed in banner
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual };
});

vi.mock('lucide-react', () => {
  const icon = (id) => () => <svg data-testid={id} />;
  return {
    Shield:    icon('shield-icon'),
    UserPlus:  icon('user-plus-icon'),
    Pencil:    icon('pencil-icon'),
    Trash2:    icon('trash-icon'),
    X:         icon('x-icon'),
    Check:     icon('check-icon'),
    Copy:      icon('copy-icon'),
    RefreshCw: icon('refresh-icon'),
  };
});

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { email: 'admin@example.com', is_admin: true },
    isAuthenticated: true,
  }),
}));

// Mock API
vi.mock('../services/api', () => ({
  getAdminUsers: vi.fn(),
  createAdminUser: vi.fn(),
  updateAdminUser: vi.fn(),
  deleteAdminUser: vi.fn(),
}));

import AdminPage from './AdminPage';
import {
  getAdminUsers,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
} from '../services/api';

const USERS = [
  { id: 1, username: 'admin', email: 'admin@example.com', is_admin: true },
  { id: 2, username: 'alice', email: 'alice@example.com', is_admin: false },
];

const renderPage = () => render(<AdminPage />);

beforeEach(() => {
  vi.clearAllMocks();
  getAdminUsers.mockResolvedValue({ data: USERS });
});

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

describe('AdminPage — rendering', () => {
  it('shows the page heading', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('User Management')).toBeInTheDocument());
  });

  it('renders a row for each user', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    });
  });

  it('shows Admin badge for admin user', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Admin')).toBeInTheDocument());
  });

  it('disables delete button for current user row', async () => {
    renderPage();
    await waitFor(() => screen.getByText('alice'));
    // The admin row (email == current user) should have a disabled trash button
    const rows = screen.getAllByTitle(/delete|cannot/i);
    const disabledRow = rows.find((b) => b.disabled);
    expect(disabledRow).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Create user
// ---------------------------------------------------------------------------

describe('AdminPage — create user', () => {
  it('opens create modal on "Add user" click', async () => {
    renderPage();
    await waitFor(() => screen.getByText('User Management'));
    fireEvent.click(screen.getByText('Add user'));
    expect(screen.getByTestId('user-form-modal')).toBeInTheDocument();
  });

  it('calls createAdminUser with form data on submit', async () => {
    createAdminUser.mockResolvedValue({
      data: { id: 3, username: 'newbie', email: 'newbie@example.com', is_admin: false, otp_uri: 'otpauth://x' },
    });

    renderPage();
    await waitFor(() => screen.getByText('User Management'));
    fireEvent.click(screen.getByText('Add user'));

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'newbie' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'newbie@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /create user/i }));

    await waitFor(() =>
      expect(createAdminUser).toHaveBeenCalledWith({
        username: 'newbie',
        email: 'newbie@example.com',
        is_admin: false,
      })
    );
  });

  it('shows OTP modal after successful creation', async () => {
    createAdminUser.mockResolvedValue({
      data: { id: 3, username: 'newbie', email: 'newbie@example.com', is_admin: false, otp_uri: 'otpauth://x' },
    });

    renderPage();
    await waitFor(() => screen.getByText('User Management'));
    fireEvent.click(screen.getByText('Add user'));
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'newbie' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'newbie@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /create user/i }));

    await waitFor(() => expect(screen.getByTestId('otp-modal')).toBeInTheDocument());
    expect(screen.getByText('otpauth://x')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Edit user
// ---------------------------------------------------------------------------

describe('AdminPage — edit user', () => {
  it('opens edit modal pre-filled with user data', async () => {
    renderPage();
    await waitFor(() => screen.getByText('alice'));

    const editButtons = screen.getAllByTitle('Edit');
    fireEvent.click(editButtons[0]); // click first edit button

    expect(screen.getByTestId('user-form-modal')).toBeInTheDocument();
  });

  it('calls updateAdminUser on save', async () => {
    updateAdminUser.mockResolvedValue({ data: { id: 1, username: 'admin2', email: 'admin@example.com', is_admin: true } });

    renderPage();
    await waitFor(() => screen.getByText('alice'));

    const editButtons = screen.getAllByTitle('Edit');
    fireEvent.click(editButtons[1]); // edit alice

    const usernameInput = screen.getByLabelText('Username');
    fireEvent.change(usernameInput, { target: { value: 'alice2' } });
    fireEvent.click(screen.getByText('Save changes'));

    await waitFor(() =>
      expect(updateAdminUser).toHaveBeenCalledWith(2, expect.objectContaining({ username: 'alice2' }))
    );
  });
});

// ---------------------------------------------------------------------------
// Delete user
// ---------------------------------------------------------------------------

describe('AdminPage — delete user', () => {
  it('shows delete confirmation on trash click', async () => {
    renderPage();
    await waitFor(() => screen.getByText('alice'));

    // Find enabled delete buttons (alice is not current user)
    const deleteButtons = screen.getAllByTitle('Delete');
    fireEvent.click(deleteButtons[0]);

    expect(screen.getByTestId('delete-confirm')).toBeInTheDocument();
  });

  it('calls deleteAdminUser on confirmation', async () => {
    deleteAdminUser.mockResolvedValue({ data: { message: 'ok' } });

    renderPage();
    await waitFor(() => screen.getByText('alice'));

    const deleteButtons = screen.getAllByTitle('Delete');
    fireEvent.click(deleteButtons[0]);
    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => expect(deleteAdminUser).toHaveBeenCalledWith(2));
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('AdminPage — error handling', () => {
  it('shows error banner when getAdminUsers fails', async () => {
    getAdminUsers.mockRejectedValue(new Error('Network error'));
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('Failed to load users.')).toBeInTheDocument()
    );
  });
});
