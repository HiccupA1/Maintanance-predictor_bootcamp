import { describe, expect, it } from 'vitest';

import {
  validateParameterForm,
  type ParameterFormValues,
} from '../../api/parameters';

const validForm: ParameterFormValues = {
  name: 'Temperature',
  unit: '°C',
  min_threshold: '10',
  max_threshold: '80',
  active: true,
  suggested_action: 'Inspect cooling system.',
};

describe('Parameter form validation', () => {
  it('rejects missing name and unit', () => {
    const errors = validateParameterForm({
      ...validForm,
      name: '',
      unit: ' ',
    });

    expect(errors.name).toBe('Name is required.');
    expect(errors.unit).toBe('Unit is required.');
  });

  it('requires at least one threshold', () => {
    const errors = validateParameterForm({
      ...validForm,
      min_threshold: '',
      max_threshold: '',
    });

    expect(errors.form).toContain('At least one');
  });

  it('rejects an inverted threshold range', () => {
    const errors = validateParameterForm({
      ...validForm,
      min_threshold: '90',
      max_threshold: '80',
    });

    expect(errors.form).toBe('Minimum threshold must not exceed maximum threshold.');
  });

  it('accepts a valid form with only one threshold', () => {
    expect(validateParameterForm({
      ...validForm,
      min_threshold: '',
    })).toEqual({});
  });
});
