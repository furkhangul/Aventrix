import { useTranslation } from "react-i18next";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { DateRangePreset } from "@/lib/types";

const OPTIONS: { value: DateRangePreset; key: string }[] = [
  { value: "today", key: "dateRange.today" },
  { value: "yesterday", key: "dateRange.yesterday" },
  { value: "7d", key: "dateRange.7d" },
  { value: "30d", key: "dateRange.30d" },
  { value: "90d", key: "dateRange.90d" },
];

export function DateRangeSelect({
  value,
  onChange,
}: {
  value: DateRangePreset;
  onChange: (value: DateRangePreset) => void;
}) {
  const { t } = useTranslation();
  return (
    <Select value={value} onValueChange={(v) => onChange(v as DateRangePreset)}>
      <SelectTrigger className="w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {t(opt.key)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
