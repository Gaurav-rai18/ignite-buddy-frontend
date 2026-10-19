import { describe, it, expect } from 'vitest';
import {
  isValidHttpsUrl,
  validateBroadcastForm,
  validateScheduleForm,
  validateBuddyState,
} from '../utils/validation';

describe('Validation Utilities', () => {
  describe('isValidHttpsUrl', () => {
    it('accepts valid HTTPS OneDrive URLs', () => {
      expect(isValidHttpsUrl('https://1drv.ms/u/s!Al7812903')).toBe(true);
      expect(isValidHttpsUrl('https://sharepoint.com/my/doc')).toBe(true);
      expect(isValidHttpsUrl('https://example.com/file')).toBe(true);
    });

    it('rejects non-HTTPS URLs and malformed strings', () => {
      expect(isValidHttpsUrl('http://insecure.com')).toBe(false);
      expect(isValidHttpsUrl('javascript:alert(1)')).toBe(false);
      expect(isValidHttpsUrl('ftp://example.com')).toBe(false);
      expect(isValidHttpsUrl('')).toBe(false);
      expect(isValidHttpsUrl(null)).toBe(false);
      expect(isValidHttpsUrl('not a url')).toBe(false);
    });
  });

  describe('validateBroadcastForm', () => {
    it('validates required fields and audience', () => {
      const invalid = validateBroadcastForm({ title: '', message: '', audience: '' });
      expect(invalid.isValid).toBe(false);
      expect(invalid.errors.title).toBeDefined();
      expect(invalid.errors.message).toBeDefined();
      expect(invalid.errors.audience).toBeDefined();
    });

    it('rejects invalid audience option', () => {
      const result = validateBroadcastForm({
        title: 'Exam info',
        message: 'Details here',
        audience: 'External visitors',
      });
      expect(result.isValid).toBe(false);
      expect(result.errors.audience).toBe('Invalid audience selection.');
    });

    it('accepts valid broadcast data', () => {
      const valid = validateBroadcastForm({
        title: 'Midterm timetable released',
        message: 'Please review the updated examination slots.',
        audience: 'All students',
      });
      expect(valid.isValid).toBe(true);
      expect(Object.keys(valid.errors).length).toBe(0);
    });

    it('enforces maximum length limits', () => {
      const longTitle = 'a'.repeat(161);
      const longMsg = 'b'.repeat(2001);
      const result = validateBroadcastForm({
        title: longTitle,
        message: longMsg,
        audience: 'First year',
      });
      expect(result.isValid).toBe(false);
      expect(result.errors.title).toBeDefined();
      expect(result.errors.message).toBeDefined();
    });
  });

  describe('validateScheduleForm', () => {
    it('validates required title, onedrive_url, and publish_at', () => {
      const result = validateScheduleForm({ title: '', onedrive_url: '', publish_at: '' });
      expect(result.isValid).toBe(false);
      expect(result.errors.title).toBeDefined();
      expect(result.errors.onedrive_url).toBeDefined();
      expect(result.errors.publish_at).toBeDefined();
    });

    it('rejects insecure or non-HTTPS URLs', () => {
      const result = validateScheduleForm({
        title: 'Syllabus PDF',
        onedrive_url: 'http://1drv.ms/abc',
        publish_at: '2026-11-01T10:00',
      });
      expect(result.isValid).toBe(false);
      expect(result.errors.onedrive_url).toContain('HTTPS');
    });

    it('accepts valid schedule inputs', () => {
      const result = validateScheduleForm({
        title: 'Semester 5 study material',
        onedrive_url: 'https://1drv.ms/u/s!Aexample',
        publish_at: '2026-11-01T10:00',
      });
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors).length).toBe(0);
    });
  });

  describe('validateBuddyState', () => {
    it('only accepts booleans', () => {
      expect(validateBuddyState(true)).toBe(true);
      expect(validateBuddyState(false)).toBe(true);
      expect(validateBuddyState('true')).toBe(false);
      expect(validateBuddyState(null)).toBe(false);
    });
  });
});
