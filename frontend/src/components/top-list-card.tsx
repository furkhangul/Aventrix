import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TopItem } from "@/lib/types";

export function TopListCard({ title, items, isLoading }: { title: string; items: TopItem[] | undefined; isLoading: boolean }) {
  const { t } = useTranslation();
  const max = items?.[0]?.count ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {isLoading ? (
          <div className="h-32 animate-pulse rounded-md bg-muted" />
        ) : !items || items.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{t("dashboard.noDataYet")}</p>
        ) : (
          items.map((item) => (
            <div key={item.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="truncate">{item.label}</span>
                <span className="text-muted-foreground">{item.count}</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${max ? (item.count / max) * 100 : 0}%` }}
                />
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
