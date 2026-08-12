import { Bell, CheckCheck, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pagination } from "@/components/ui/pagination";
import { Switch } from "@/components/ui/switch";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import {
  useDeleteNotification,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotificationPreferences,
  useNotifications,
  useUpdateNotificationPreferences,
} from "@/hooks/use-notifications";
import { formatDateTime } from "@/lib/utils";
import type { Notification } from "@/lib/types";

const PREFERENCE_TYPES: { type: string; labelKey: string }[] = [
  { type: "LINK_EXPIRED", labelKey: "notifications.prefLinkExpired" },
  { type: "LINK_FIRST_VISIT", labelKey: "notifications.prefLinkFirstVisit" },
  { type: "WEBHOOK_DELIVERY_FAILED", labelKey: "notifications.prefWebhookFailed" },
  { type: "SECURITY_SCAN_WARNING", labelKey: "notifications.prefSecurityWarning" },
];

function NotificationRow({ notification }: { notification: Notification }) {
  const { t } = useTranslation();
  const markRead = useMarkNotificationRead();
  const deleteNotification = useDeleteNotification();

  return (
    <div className={`flex items-start justify-between gap-3 rounded-md border p-3 ${notification.is_read ? "border-border" : "border-primary/30 bg-primary/5"}`}>
      <div>
        <p className="text-sm font-medium">{notification.title}</p>
        <p className="text-sm text-muted-foreground">{notification.message}</p>
        <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(notification.created_at)}</p>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {!notification.is_read && (
          <Button variant="ghost" size="icon" aria-label={t("notifications.markAllRead")} onClick={() => markRead.mutate(notification.id)}>
            <CheckCheck className="h-4 w-4" />
          </Button>
        )}
        <Button variant="ghost" size="icon" aria-label={t("common.delete")} onClick={() => deleteNotification.mutate(notification.id)}>
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
    </div>
  );
}

function PreferencesPanel() {
  const { t } = useTranslation();
  const { data } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();
  const preferences = data?.preferences ?? {};

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("notifications.preferencesTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {PREFERENCE_TYPES.map((pref) => (
          <div key={pref.type} className="flex items-center justify-between">
            <p className="text-sm">{t(pref.labelKey)}</p>
            <Switch
              checked={preferences[pref.type] !== false}
              onCheckedChange={(checked) => updatePreferences.mutate({ [pref.type]: checked })}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function NotificationsPage() {
  const { t } = useTranslation();
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, refetch } = useNotifications({ page, unreadOnly });
  const markAllRead = useMarkAllNotificationsRead();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("notifications.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("notifications.unreadCount", { count: data?.unread_count ?? 0 })}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setUnreadOnly((v) => !v)}>
            {unreadOnly ? t("notifications.showAll") : t("notifications.showUnreadOnly")}
          </Button>
          <Button variant="outline" size="sm" onClick={() => markAllRead.mutate()} disabled={markAllRead.isPending}>
            <CheckCheck className="h-4 w-4" />
            {t("notifications.markAllRead")}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr,320px]">
        <div className="space-y-3">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : !data || data.items.length === 0 ? (
            <EmptyState icon={Bell} title={t("notifications.emptyTitle")} description={t("notifications.emptyDescription")} />
          ) : (
            <>
              {data.items.map((notification) => (
                <NotificationRow key={notification.id} notification={notification} />
              ))}
              <Pagination page={page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
            </>
          )}
        </div>
        <PreferencesPanel />
      </div>
    </div>
  );
}
