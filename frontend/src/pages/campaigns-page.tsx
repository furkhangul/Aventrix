import { FolderKanban } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { CreateCampaignDialog } from "@/components/campaigns/campaign-dialogs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { useCampaigns } from "@/hooks/use-campaigns";
import { formatDate, formatNumber } from "@/lib/utils";
import type { CampaignStatus } from "@/lib/types";

const STATUS_VARIANT: Record<CampaignStatus, "success" | "secondary" | "outline"> = {
  ACTIVE: "success",
  PAUSED: "secondary",
  ARCHIVED: "outline",
};

const STATUS_LABEL_KEY: Record<CampaignStatus, string> = {
  ACTIVE: "campaignDetail.statusActive",
  PAUSED: "campaignDetail.statusPaused",
  ARCHIVED: "campaignDetail.statusArchived",
};

export function CampaignsPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<CampaignStatus | "all">("all");
  const { data, isLoading, isError, refetch } = useCampaigns({
    page,
    search: search || undefined,
    status: status === "all" ? undefined : status,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("campaigns.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("campaigns.subtitle")}</p>
        </div>
        <CreateCampaignDialog />
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          placeholder={t("campaigns.searchPlaceholder")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="max-w-sm"
        />
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v as CampaignStatus | "all");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("campaigns.allStatuses")}</SelectItem>
            <SelectItem value="ACTIVE">{t("campaignDetail.statusActive")}</SelectItem>
            <SelectItem value="PAUSED">{t("campaignDetail.statusPaused")}</SelectItem>
            <SelectItem value="ARCHIVED">{t("campaignDetail.statusArchived")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title={t("campaigns.emptyTitle")}
          description={t("campaigns.emptyDescription")}
          action={<CreateCampaignDialog />}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((campaign) => (
              <Link key={campaign.id} to={`/projects/${campaign.id}`}>
                <Card className="h-full transition-shadow hover:shadow-md">
                  <CardContent className="flex h-full flex-col gap-3 p-5">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-medium leading-tight">{campaign.name}</h3>
                      <Badge variant={STATUS_VARIANT[campaign.status]}>{t(STATUS_LABEL_KEY[campaign.status])}</Badge>
                    </div>
                    {campaign.description && (
                      <p className="line-clamp-2 text-sm text-muted-foreground">{campaign.description}</p>
                    )}
                    {campaign.tags && campaign.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {campaign.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="font-normal">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <div className="mt-auto grid grid-cols-3 gap-2 border-t border-border pt-3 text-center">
                      <div>
                        <p className="text-sm font-semibold">{formatNumber(campaign.link_count)}</p>
                        <p className="text-[11px] text-muted-foreground">{t("campaigns.links")}</p>
                      </div>
                      <div>
                        <p className="text-sm font-semibold">{formatNumber(campaign.total_visits)}</p>
                        <p className="text-[11px] text-muted-foreground">{t("campaigns.visits")}</p>
                      </div>
                      <div>
                        <p className="text-sm font-semibold">{formatNumber(campaign.unique_visitors)}</p>
                        <p className="text-[11px] text-muted-foreground">{t("campaigns.uniques")}</p>
                      </div>
                    </div>
                    <p className="text-[11px] text-muted-foreground">{t("campaigns.created", { date: formatDate(campaign.created_at) })}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
          <Pagination page={page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
