import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BroadcastForm } from '../components/broadcast/BroadcastForm';
import { ScheduleForm } from '../components/schedule/ScheduleForm';
import { BuddyDetails } from '../components/buddy/BuddyDetails';
import { BuddyHero } from '../components/buddy/BuddyHero';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { ProfileDropdown } from '../components/layout/ProfileDropdown';
import { NotificationsDropdown } from '../components/layout/NotificationsDropdown';

describe('Frontend Component Tests', () => {
  describe('BroadcastForm', () => {
    it('disables submit button when title or message is empty', () => {
      render(
        <BroadcastForm
          form={{ title: '', message: '', audience: 'All students' }}
          formErrors={{}}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      const submitBtn = screen.getByRole('button', { name: /publish broadcast/i });
      expect(submitBtn).toBeDisabled();
    });

    it('enables submit button and calls onSubmit when valid', async () => {
      const user = userEvent.setup();
      const handleSubmit = vi.fn();

      render(
        <BroadcastForm
          form={{ title: 'Exam update', message: 'Exam starts at 9am', audience: 'All students' }}
          formErrors={{}}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onSubmit={handleSubmit}
        />
      );

      const submitBtn = screen.getByRole('button', { name: /publish broadcast/i });
      expect(submitBtn).not.toBeDisabled();

      await user.click(submitBtn);
      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });

    it('opens and closes the preview modal when Preview button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BroadcastForm
          form={{ title: 'Auditorium Booking', message: 'Bookings open from 10am', audience: 'All students' }}
          formErrors={{}}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      const previewBtn = screen.getByRole('button', { name: /preview/i });
      await user.click(previewBtn);

      expect(screen.getByRole('dialog', { name: /announcement preview/i })).toBeInTheDocument();
      expect(screen.getByText('Auditorium Booking')).toBeInTheDocument();

      const closeBtn = screen.getByRole('button', { name: /close preview modal/i });
      await user.click(closeBtn);

      expect(screen.queryByRole('dialog', { name: /announcement preview/i })).not.toBeInTheDocument();
    });

    it('renders validation errors when provided', () => {
      render(
        <BroadcastForm
          form={{ title: '', message: '', audience: 'All students' }}
          formErrors={{ title: 'Title is required.' }}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Title is required.')).toBeInTheDocument();
    });
  });

  describe('ScheduleForm', () => {
    it('disables schedule link button when fields are incomplete', () => {
      render(
        <ScheduleForm
          form={{ title: '', onedrive_url: '', publish_date: '', publish_time: '' }}
          formErrors={{}}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onCancel={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      const submitBtn = screen.getByRole('button', { name: /schedule link/i });
      expect(submitBtn).toBeDisabled();
    });

    it('calls onCancel when Cancel button is clicked', async () => {
      const user = userEvent.setup();
      const handleCancel = vi.fn();

      render(
        <ScheduleForm
          form={{ title: 'Notes', onedrive_url: 'https://1drv.ms/test', publish_date: '2026-11-01', publish_time: '10:00' }}
          formErrors={{}}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onCancel={handleCancel}
          onSubmit={vi.fn()}
        />
      );

      const cancelBtn = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelBtn);
      expect(handleCancel).toHaveBeenCalledTimes(1);
    });

    it('displays validation error for invalid OneDrive link', () => {
      render(
        <ScheduleForm
          form={{ title: 'Notes', onedrive_url: 'http://insecure.com', publish_date: '2026-11-01', publish_time: '10:00' }}
          formErrors={{ onedrive_url: 'Please provide a valid HTTPS URL.' }}
          isSubmitting={false}
          onChangeField={vi.fn()}
          onCancel={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Please provide a valid HTTPS URL.')).toBeInTheDocument();
    });
  });

  describe('Buddy Components', () => {
    it('displays active/paused state and triggers toggle on switch click in BuddyDetails', async () => {
      const user = userEvent.setup();
      const handleToggle = vi.fn();

      const { rerender } = render(
        <BuddyDetails buddy={true} isUpdating={false} onToggleBuddy={handleToggle} />
      );

      expect(screen.getByText('Enabled')).toBeInTheDocument();
      const switchBtn = screen.getByRole('switch');
      expect(switchBtn).toHaveAttribute('aria-checked', 'true');

      await user.click(switchBtn);
      expect(handleToggle).toHaveBeenCalledTimes(1);

      rerender(<BuddyDetails buddy={false} isUpdating={false} onToggleBuddy={handleToggle} />);
      expect(screen.getByText('Disabled')).toBeInTheDocument();
      expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'false');
    });

    it('BuddyHero renders enterprise action button and toggles state', async () => {
      const user = userEvent.setup();
      const handleToggle = vi.fn();

      const { rerender } = render(
        <BuddyHero buddy={true} isUpdating={false} onToggleBuddy={handleToggle} />
      );

      const offBtn = screen.getByRole('button', { name: /turn buddy off/i });
      await user.click(offBtn);
      expect(handleToggle).toHaveBeenCalledTimes(1);

      rerender(<BuddyHero buddy={false} isUpdating={false} onToggleBuddy={handleToggle} />);
      expect(screen.getByRole('button', { name: /turn buddy on/i })).toBeInTheDocument();
    });
  });

  describe('Dropdown Menus', () => {
    it('ProfileDropdown renders profile actions and triggers sign out', async () => {
      const user = userEvent.setup();
      const handleSignOut = vi.fn();
      const handleClose = vi.fn();

      render(
        <ProfileDropdown
          isOpen={true}
          onClose={handleClose}
          onSignOut={handleSignOut}
        />
      );

      expect(screen.getByText('Administrator')).toBeInTheDocument();
      expect(screen.getByText('Admin Profile')).toBeInTheDocument();

      const signOutBtn = screen.getByRole('menuitem', { name: /sign out/i });
      await user.click(signOutBtn);

      expect(handleSignOut).toHaveBeenCalledTimes(1);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('NotificationsDropdown renders notifications and marks all as read', async () => {
      const user = userEvent.setup();
      const handleClose = vi.fn();

      render(
        <NotificationsDropdown
          isOpen={true}
          onClose={handleClose}
          broadcasts={[{ id: 1, title: 'First Announcement' }]}
        />
      );

      expect(screen.getByText(/First Announcement/i)).toBeInTheDocument();

      const markBtn = screen.getByRole('button', { name: /mark all as read/i });
      await user.click(markBtn);

      expect(screen.getByText(/No unread notifications/i)).toBeInTheDocument();
    });
  });

  describe('ErrorBanner', () => {
    it('renders error message and retry button', async () => {
      const user = userEvent.setup();
      const handleRetry = vi.fn();

      render(
        <ErrorBanner
          message="Unable to load announcements. Please try again."
          onRetry={handleRetry}
        />
      );

      expect(screen.getByText(/Unable to load announcements/i)).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      await user.click(retryBtn);
      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });
});
