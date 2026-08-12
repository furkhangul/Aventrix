import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/logo";

export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <Logo mark className="h-12 w-12" />
      <h1 className="text-2xl font-semibold">{t("notFound.title")}</h1>
      <p className="max-w-sm text-sm text-muted-foreground">{t("notFound.body")}</p>
      <Button asChild>
        <Link to="/">{t("notFound.goHome")}</Link>
      </Button>
    </div>
  );
}
