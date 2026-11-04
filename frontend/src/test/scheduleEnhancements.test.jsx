import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { validateTimeSlot, timeStringToMinutes } from '../utils/validation';
import { ScheduleGridBuilder } from '../components/schedule/ScheduleGridBuilder';
import { ExcelUpload } from '../components/schedule/ExcelUpload';
import { BatchManagerModal } from '../components/schedule/BatchManagerModal';
import { TimeSlotManagerModal } from '../components/schedule/TimeSlotManagerModal';
import {
  DEFAULT_SCHEDULE_LOCATIONS,
  DEFAULT_SCHEDULE_DAYS,
  DEFAULT_SCHEDULE_TIME_SLOTS,
} from '../constants';

describe('Schedule Enhancements Tests', () => {
  describe('Time Slot Validation', () => {
    it('converts 12-hour AM/PM time strings to minutes', () => {
      expect(timeStringToMinutes('9:00 AM')).toBe(540);
      expect(timeStringToMinutes('12:00 PM')).toBe(720);
      expect(timeStringToMinutes('1:30 PM')).toBe(810);
      expect(timeStringToMinutes('12:00 AM')).toBe(0);
    });

    it('rejects missing start or end time', () => {
      const res = validateTimeSlot('', '11:00 AM');
      expect(res.isValid).toBe(false);
      expect(res.errors.startTime).toBeDefined();
    });

    it('rejects end time earlier than or equal to start time', () => {
      const res = validateTimeSlot('11:00 AM', '9:00 AM');
      expect(res.isValid).toBe(false);
      expect(res.errors.endTime).toBe('End time must be later than start time.');

      const same = validateTimeSlot('10:00 AM', '10:00 AM');
      expect(same.isValid).toBe(false);
    });

    it('rejects overlapping time slots', () => {
      const existing = [
        { id: 1, start_time: '9:00 AM', end_time: '11:00 AM' },
        { id: 2, start_time: '11:30 AM', end_time: '1:30 PM' },
      ];
      // 10:00 AM to 12:00 PM overlaps with both
      const res = validateTimeSlot('10:00 AM', '12:00 PM', existing);
      expect(res.isValid).toBe(false);
      expect(res.errors.overlap).toBeDefined();
    });

    it('accepts valid non-overlapping time range', () => {
      const existing = [
        { id: 1, start_time: '9:00 AM', end_time: '11:00 AM' },
        { id: 2, start_time: '11:30 AM', end_time: '1:30 PM' },
      ];
      const res = validateTimeSlot('2:00 PM', '4:00 PM', existing);
      expect(res.isValid).toBe(true);
      expect(Object.keys(res.errors).length).toBe(0);
    });
  });

  describe('ScheduleGridBuilder Seven Locations & Dynamic Batches', () => {
    const mockConfig = {
      locations: [
        { id: 1, name: 'Lab 1', badge: 'Hardware' },
        { id: 2, name: 'Lab 2', badge: 'Software' },
        { id: 3, name: 'Lab 3', badge: 'Data & AI' },
        { id: 4, name: 'Lab 4', badge: 'Cloud Ops' },
        { id: 5, name: 'Work Area', badge: 'Work Area' },
        { id: 6, name: 'TR1', badge: 'TR1' },
        { id: 7, name: 'TR2', badge: 'TR2' },
      ],
      weekdays: [
        { id: 1, name: 'Monday' },
        { id: 2, name: 'Tuesday' },
        { id: 3, name: 'Wednesday' },
        { id: 4, name: 'Thursday' },
        { id: 5, name: 'Friday' },
      ],
      time_slots: [
        { id: 1, label: '9:00 AM – 11:00 AM', start_time: '9:00 AM', end_time: '11:00 AM' },
        { id: 2, label: '11:30 AM – 1:30 PM', start_time: '11:30 AM', end_time: '1:30 PM' },
      ],
      batches: [
        {
          id: 1,
          name: 'Batch A',
          code: 'A',
          subbatches: [
            { id: 1, name: 'A1', code: 'a1' },
            { id: 2, name: 'A2', code: 'a2' },
          ],
        },
      ],
    };

    it('renders all seven locations and excludes Incubator', () => {
      render(
        <ScheduleGridBuilder
          value={{ day: 'Monday', grid: {} }}
          onChange={vi.fn()}
          disabled={false}
          config={mockConfig}
        />
      );

      // Verify all 7 locations are in the table
      expect(screen.getByText('Lab 1')).toBeInTheDocument();
      expect(screen.getByText('Lab 2')).toBeInTheDocument();
      expect(screen.getByText('Lab 3')).toBeInTheDocument();
      expect(screen.getByText('Lab 4')).toBeInTheDocument();
      expect(screen.getAllByText('Work Area').length).toBeGreaterThan(0);
      expect(screen.getAllByText('TR1').length).toBeGreaterThan(0);
      expect(screen.getAllByText('TR2').length).toBeGreaterThan(0);

      // Incubator should NOT be present
      expect(screen.queryByText('Incubator')).not.toBeInTheDocument();
    });

    it('renders only 5 days (Monday to Friday) and excludes Saturday and Sunday', () => {
      render(
        <ScheduleGridBuilder
          value={{ day: 'Monday', grid: {} }}
          onChange={vi.fn()}
          disabled={false}
          config={mockConfig}
        />
      );

      expect(screen.getByText('Monday')).toBeInTheDocument();
      expect(screen.getByText('Friday')).toBeInTheDocument();
      expect(screen.queryByText('Saturday')).not.toBeInTheDocument();
      expect(screen.queryByText('Sunday')).not.toBeInTheDocument();
    });

    it('opens BatchManagerModal when + Add Batch is clicked', async () => {
      const user = userEvent.setup();
      render(
        <ScheduleGridBuilder
          value={{ day: 'Monday', grid: {} }}
          onChange={vi.fn()}
          disabled={false}
          config={mockConfig}
        />
      );

      const addBatchBtn = screen.getByRole('button', { name: /\+ add batch/i });
      await user.click(addBatchBtn);

      expect(screen.getByRole('dialog', { name: /manage dynamic batches/i })).toBeInTheDocument();
    });

    it('opens TimeSlotManagerModal when + Add Time Slot is clicked', async () => {
      const user = userEvent.setup();
      render(
        <ScheduleGridBuilder
          value={{ day: 'Monday', grid: {} }}
          onChange={vi.fn()}
          disabled={false}
          config={mockConfig}
        />
      );

      const addSlotBtn = screen.getByRole('button', { name: /\+ add time slot/i });
      await user.click(addSlotBtn);

      expect(screen.getByRole('dialog', { name: /manage dynamic time slots/i })).toBeInTheDocument();
    });
  });

  describe('ExcelUpload Component', () => {
    it('renders template download button and dropzone', () => {
      render(
        <ExcelUpload
          file={null}
          fileName=""
          fileSize={null}
          parsedData={null}
          onFileSelect={vi.fn()}
          onFileRemove={vi.fn()}
          disabled={false}
        />
      );

      expect(screen.getByRole('button', { name: /download template/i })).toBeInTheDocument();
      expect(screen.getByText(/drag and drop your timetable excel file here/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /browse files/i })).toBeInTheDocument();
    });

    it('renders verified file card and preview table when parsedData is provided', () => {
      const mockParsed = {
        total_rows_parsed: 5,
        days_found: ['Monday'],
        selected_day: 'Monday',
        grid: {
          '9:00 AM – 11:00 AM': {
            'Lab 1': { topic: 'Microprocessors', subbatches: ['a1', 'a2'] },
          },
        },
      };

      const mockFile = new File(['dummy content'], 'Week14.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      render(
        <ExcelUpload
          file={mockFile}
          fileName="Week14.xlsx"
          fileSize={12450}
          parsedData={mockParsed}
          onFileSelect={vi.fn()}
          onFileRemove={vi.fn()}
          disabled={false}
        />
      );

      expect(screen.getByText('Week14.xlsx')).toBeInTheDocument();
      expect(screen.getByText(/verified & ready/i)).toBeInTheDocument();
      expect(screen.getByText('Microprocessors')).toBeInTheDocument();
      expect(screen.getByText('A1')).toBeInTheDocument();
      expect(screen.getByText('A2')).toBeInTheDocument();
    });
  });

  describe('BatchManagerModal', () => {
    it('shows error when creating batch with duplicate code', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        batches: [{ id: 1, name: 'Batch A', code: 'A', subbatches: [] }],
      };

      render(
        <BatchManagerModal
          isOpen={true}
          onClose={vi.fn()}
          config={mockConfig}
          onAddBatch={vi.fn()}
          onRemoveBatch={vi.fn()}
          onAddSubBatch={vi.fn()}
          onRemoveSubBatch={vi.fn()}
        />
      );

      const codeInput = screen.getByPlaceholderText('e.g. D');
      await user.type(codeInput, 'A');

      const submitBtn = screen.getByRole('button', { name: /\+ add batch/i });
      await user.click(submitBtn);

      expect(screen.getByText(/already exists/i)).toBeInTheDocument();
    });
  });
});
