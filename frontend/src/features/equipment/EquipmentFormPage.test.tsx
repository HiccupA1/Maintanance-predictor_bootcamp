import { describe, expect, it } from 'vitest';

import { validateEquipmentForm } from '../../hooks/useEquipment';

describe('Equipment form validation', () => {
  it('rejects missing required fields', () => {
    const errors = validateEquipmentForm({
      equipment_id: '',
      name: '',
      location: '',
      type: '',
      criticality: '',
    });

    expect(errors.equipment_id).toBeTruthy();
    expect(errors.name).toBeTruthy();
    expect(errors.location).toBeTruthy();
    expect(errors.type).toBeTruthy();
    expect(errors.criticality).toBeTruthy();
  });

  it.each(['0', '6', '2.5', 'abc'])('rejects invalid criticality %s', (criticality) => {
    const errors = validateEquipmentForm({
      equipment_id: 'EQ-001',
      name: 'Compressor',
      location: 'Plant A',
      type: 'Rotary',
      criticality,
    });

    expect(errors.criticality).toBe('Criticality must be an integer from 1 to 5.');
  });

  it('accepts a valid equipment form', () => {
    expect(validateEquipmentForm({
      equipment_id: 'EQ-001',
      name: 'Compressor',
      location: 'Plant A',
      type: 'Rotary',
      criticality: '4',
    })).toEqual({});
  });
});
