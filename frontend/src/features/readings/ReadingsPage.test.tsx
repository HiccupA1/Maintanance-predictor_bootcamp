import { describe, expect, it } from 'vitest';

import {
  validateReadingCorrection,
  validateReadingForm,
  type ReadingFormValues,
} from '../../api/readings';

const validForm: ReadingFormValues = {
  equipment_id: 'EQ-001',
  parameter_id: 'parameter-1',
  value: '72.4',
};

describe('Reading form validation', () => {
  it('requires equipment, parameter, and value', () => {
    const errors = validateReadingForm({
      equipment_id: '',
      parameter_id: ' ',
      value: '',
    });

    expect(errors.equipment_id).toBe('Equipment is required.');
    expect(errors.parameter_id).toBe('Parameter is required.');
    expect(errors.value).toBe('Value is required.');
  });

  it('accepts non-numeric reading values', () => {
    expect(
      validateReadingForm({
        ...validForm,
        value: 'abnormal vibration observed',
      }),
    ).toEqual({});
  });
});

describe('Reading correction validation', () => {
  it('requires a replacement value and modification reason', () => {
    const errors = validateReadingCorrection({
      value: '',
      modification_reason: ' ',
    });

    expect(errors.value).toBe('Value is required.');
    expect(errors.modification_reason).toBe('Modification reason is required.');
  });

  it('accepts a valid correction', () => {
    expect(
      validateReadingCorrection({
        value: '73.1',
        modification_reason: 'Corrected transcription error',
      }),
    ).toEqual({});
  });
});
