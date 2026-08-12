import { AlertTriangle, ArrowLeft, Link2, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { EditCampaignDialog } from "@/components/campaigns/campaign-dialogs";
import { CreateLinkDialog } from "@/components/links/create-link-dialog";
import { LinkTable } from "@/components/links/link-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { useCampaign, useDeleteCampaign } from "@/hooks/use-campaigns";
import { useLinks } from "@/hooks/use-links";
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

export function CampaignDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: campaign, isLoading, isError, refetch } = useCampaign(id);
  const { data: linksData, isLoading: linksLoading } = useLinks({ campaignId: id, pageSize: 50 });
  const deleteCampaign = useDeleteCampaign();
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (isLoading) return <LoadingState />;
  if (isError || !campaign) return <ErrorState onRetry={() => refetch()} />;

  return (
    <div className="space-y-6">
      <Link to="/projects" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> {t("campaignDetail.backToCampaigns")}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">{campaign.name}</h1>
            <Badge variant={STATUS_VARIANT[campaign.status]}>{t(STATUS_LABEL_KEY[campaign.status])}</Badge>
          </div>
          {campaign.description && <p className="mt-1 text-sm text-muted-foreground">{campaign.description}</p>}
          {campaign.tags && campaign.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {campaign.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="font-normal">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          <p className="mt-1 text-xs text-muted-foreground">{t("campaignDetail.created", { date: formatDate(campaign.created_at) })}</p>
        </div>
        <div className="flex gap-2">
          <EditCampaignDialog campaign={campaign} />
          <Button variant="outline" size="sm" onClick={() => setConfirmDelete(true)}>
            <Trash2 className="h-3.5 w-3.5 text-destructive" /> {t("campaignDetail.delete")}
          </Button>
        </div>
      </div>

      {campaign.status !== "ACTIVE" && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 p-3 text-sm text-warning-foreground">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            {campaign.status === "PAUSED"
              ? t("campaignDetail.pauseNotice", { count: campaign.link_count })
              : t("campaignDetail.archiveNotice", { count: campaign.link_count })}
          </p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">{t("campaignDetail.links")}</p>
            <p className="mt-1 text-2xl font-semibold">{formatNumber(campaign.link_count)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">{t("campaignDetail.totalVisits")}</p>
            <p className="mt-1 text-2xl font-semibold">{formatNumber(campaign.total_visits)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-sm text-muted-foreground">{t("campaignDetail.uniqueVisitors")}</p>
            <p className="mt-1 text-2xl font-semibold">{formatNumber(campaign.unique_visitors)}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">{t("campaignDetail.linksInCampaign")}</h2>
        {campaign.status !== "ARCHIVED" && <CreateLinkDialog defaultCampaignId={campaign.id} />}
      </div>

      {linksLoading ? (
        <LoadingState />
      ) : !linksData || linksData.items.length === 0 ? (
        <EmptyState
          icon={Link2}
          title={t("campaignDetail.noLinksYet")}
          action={campaign.status !== "ARCHIVED" ? <CreateLinkDialog defaultCampaignId={campaign.id} /> : undefined}
        />
      ) : (
        <LinkTable links={linksData.items} />
      )}

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("campaignDetail.deleteConfirmTitle")}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            {t("campaignDetail.deleteConfirmBody", { name: campaign.name, count: campaign.link_count })}
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="destructive"
              disabled={deleteCampaign.isPending}
              onClick={() => deleteCampaign.mutate(campaign.id, { onSuccess: () => navigate("/projects") })}
            >
              {t("campaignDetail.deleteCampaign")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
