import { Link2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CreateLinkDialog } from "@/components/links/create-link-dialog";
import { LinkTable } from "@/components/links/link-table";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { useCampaigns } from "@/hooks/use-campaigns";
import { useLinks } from "@/hooks/use-links";

export function LinksPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [campaignId, setCampaignId] = useState("all");
  const { data: campaignsData } = useCampaigns({ pageSize: 100 });
  const { data, isLoading, isError, refetch } = useLinks({
    page,
    search: search || undefined,
    campaignId: campaignId === "all" ? undefined : campaignId,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("links.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("links.subtitle")}</p>
        </div>
        <CreateLinkDialog />
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          placeholder={t("links.searchPlaceholder")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="max-w-sm"
        />
        {campaignsData && campaignsData.items.length > 0 && (
          <Select
            value={campaignId}
            onValueChange={(v) => {
              setCampaignId(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-56">
              <SelectValue placeholder={t("links.allCampaigns")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("links.allCampaigns")}</SelectItem>
              {campaignsData.items.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={Link2}
          title={t("links.emptyTitle")}
          description={t("links.emptyDescription")}
          action={<CreateLinkDialog />}
        />
      ) : (
        <>
          <LinkTable links={data.items} />
          <Pagination page={page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
