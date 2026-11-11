import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { isRequestCancellation, formatErrorMessage } from '../src/utils/error.js';

describe('Error & Cancellation Handling Tests', () => {
  it('correctly identifies Axios CanceledError as request cancellation', () => {
    const axiosCancelError = {
      name: 'CanceledError',
      message: 'canceled',
      code: 'ERR_CANCELED',
    };
    assert.equal(isRequestCancellation(axiosCancelError), true);
    // Should produce empty message so banner does not display
    assert.equal(formatErrorMessage(axiosCancelError), '');
  });

  it('correctly identifies DOM AbortError as request cancellation', () => {
    const abortError = new Error('The user aborted a request.');
    abortError.name = 'AbortError';
    assert.equal(isRequestCancellation(abortError), true);
    assert.equal(formatErrorMessage(abortError), '');
  });

  it('correctly identifies plain string message canceled as cancellation', () => {
    const plainCanceled = { message: 'canceled' };
    assert.equal(isRequestCancellation(plainCanceled), true);
    assert.equal(formatErrorMessage(plainCanceled), '');
  });

  it('preserves genuine network errors', () => {
    const networkErr = new Error('Network Error');
    assert.equal(isRequestCancellation(networkErr), false);
    const msg = formatErrorMessage(networkErr);
    assert.match(msg, /Cannot connect to the backend/);
  });

  it('formats HTTP 401, 403, 404, 500 status codes with clear guidance', () => {
    assert.match(formatErrorMessage({ status: 401 }), /Session expired/);
    assert.match(formatErrorMessage({ status: 403 }), /permission/);
    assert.match(formatErrorMessage({ status: 404 }), /not found/);
    assert.match(formatErrorMessage({ status: 500 }), /Server error/);
  });

  it('formats DRF validation field error objects', () => {
    const drfError = {
      status: 400,
      details: {
        title: ['This field is required.'],
        cohort_id: ['Invalid cohort selected.'],
      },
    };
    const msg = formatErrorMessage(drfError);
    assert.match(msg, /title: This field is required\./);
    assert.match(msg, /cohort_id: Invalid cohort selected\./);
  });
});

