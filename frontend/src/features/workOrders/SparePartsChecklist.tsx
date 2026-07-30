import { Button } from '../../components/ui/Button';
import type { WorkOrderPartLineInput } from '../../types/workOrders';

interface SparePartsChecklistProps {
  parts: WorkOrderPartLineInput[];
  onChange: (parts: WorkOrderPartLineInput[]) => void;
  disabled?: boolean;
}

// PUBLIC_INTERFACE
export function SparePartsChecklist({
  parts,
  onChange,
  disabled = false,
}: SparePartsChecklistProps) {
  /**
   * Render and edit spare-part lines used by work-order closure.
   *
   * @param parts Current spare-part lines.
   * @param onChange Callback invoked with edited lines.
   * @param disabled Whether editing controls are disabled.
   */
  const updatePart = (
    index: number,
    changes: Partial<WorkOrderPartLineInput>,
  ) => {
    onChange(
      parts.map((part, partIndex) =>
        partIndex === index ? { ...part, ...changes } : part,
      ),
    );
  };

  const addPart = () => {
    onChange([...parts, { part_name: '', used: true, notes: '' }]);
  };

  const removePart = (index: number) => {
    onChange(parts.filter((_, partIndex) => partIndex !== index));
  };

  return (
    <div className="space-y-3" data-testid="spare-parts-checklist">
      {parts.length === 0 && (
        <p className="text-sm text-slate-600">
          Add a part line, or add <span className="font-medium">N/A</span> when
          no spare part was used.
        </p>
      )}

      {parts.map((part, index) => (
        <div
          className="rounded-md border border-slate-200 bg-slate-50 p-3"
          key={`${index}-${part.part_name}`}
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto]">
            <label className="text-sm text-slate-700">
              Part name
              <input
                aria-label={`Part name ${index + 1}`}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                disabled={disabled}
                onChange={(event) =>
                  updatePart(index, { part_name: event.target.value })
                }
                value={part.part_name}
              />
            </label>

            <label className="flex items-end gap-2 pb-2 text-sm text-slate-700">
              <input
                aria-label={`Part used ${index + 1}`}
                checked={part.used}
                disabled={disabled}
                onChange={(event) =>
                  updatePart(index, { used: event.target.checked })
                }
                type="checkbox"
              />
              Used
            </label>
          </div>

          <label className="mt-3 block text-sm text-slate-700">
            Notes
            <input
              aria-label={`Part notes ${index + 1}`}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
              disabled={disabled}
              onChange={(event) =>
                updatePart(index, { notes: event.target.value })
              }
              value={part.notes ?? ''}
            />
          </label>

          {!disabled && (
            <button
              className="mt-2 text-xs font-medium text-red-700 hover:underline"
              onClick={() => removePart(index)}
              type="button"
            >
              Remove line
            </button>
          )}
        </div>
      ))}

      {!disabled && (
        <Button onClick={addPart} type="button" variant="secondary">
          Add part line
        </Button>
      )}
    </div>
  );
}
