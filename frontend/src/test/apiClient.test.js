import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, ApiError } from '../services/apiClient';

describe('apiClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('performs successful GET request and returns JSON', async () => {
    const mockData = { broadcast_count: 5, scheduled_count: 2 };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: () => Promise.resolve(JSON.stringify(mockData)),
    });

    const result = await apiClient.get('/dashboard/');
    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/dashboard/'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('performs successful POST request with JSON body', async () => {
    const payload = { title: 'Exam update', message: 'Details', audience: 'All students' };
    const responseData = { id: 1, ...payload };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      text: () => Promise.resolve(JSON.stringify(responseData)),
    });

    const result = await apiClient.post('/broadcasts/', payload);
    expect(result).toEqual(responseData);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/broadcasts/'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });

  it('throws ApiError on HTTP 400 with detail from server', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      text: () => Promise.resolve(JSON.stringify({ detail: 'enabled must be true or false' })),
    });

    await expect(apiClient.patch('/settings/buddy/', { enabled: 'invalid' })).rejects.toThrow(
      'enabled must be true or false'
    );
  });

  it('handles 204 No Content gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      text: () => Promise.resolve(''),
    });

    const result = await apiClient.delete('/schedules/1/');
    expect(result).toBeNull();
  });

  it('handles network failure with readable ApiError', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiClient.get('/dashboard/')).rejects.toThrow('Failed to fetch');
  });
});
