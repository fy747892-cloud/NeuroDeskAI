"use client";

import { CustomFieldDefinition } from "@/lib/api";

export function CustomFieldsForm({
  definitions,
  values,
  onChange,
}: {
  definitions: CustomFieldDefinition[];
  values: Record<string, unknown>;
  onChange: (fieldKey: string, value: unknown) => void;
}) {
  if (definitions.length === 0) {
    return null;
  }

  return (
    <>
      {definitions.map((definition) => (
        <div key={definition.id} className="flex flex-col gap-1">
          <label className="text-[11px] text-on-surface-variant font-bold uppercase tracking-wide">
            {definition.label}
            {definition.is_required ? <span className="text-error"> *</span> : null}
          </label>
          <CustomFieldInput
            definition={definition}
            value={values[definition.field_key]}
            onChange={(value) => onChange(definition.field_key, value)}
          />
        </div>
      ))}
    </>
  );
}

function CustomFieldInput({
  definition,
  value,
  onChange,
}: {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const inputClassName =
    "w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm";

  switch (definition.field_type) {
    case "number":
      return (
        <input
          type="number"
          className={inputClassName}
          value={typeof value === "number" ? value : ""}
          onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
        />
      );
    case "date":
      return (
        <input
          type="date"
          className={inputClassName}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value || undefined)}
        />
      );
    case "boolean":
      return (
        <input
          type="checkbox"
          className="w-5 h-5"
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
        />
      );
    case "select":
      return (
        <select
          className={inputClassName}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value || undefined)}
        >
          <option value="">--</option>
          {(definition.options ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    default:
      return (
        <input
          type="text"
          className={inputClassName}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value || undefined)}
        />
      );
  }
}
