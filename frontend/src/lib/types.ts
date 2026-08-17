export type UserRole = "SUPER_ADMIN" | "ADMIN" | "MANAGER" | "USER" | "VIEWER";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  is_active: boolean;
  is_email_verified: boolean;
  is_2fa_enabled: boolean;
  created_at: string;
}

export interface LoginResult {
  requires_2fa: boolean;
  two_factor_pending_token: string | null;
  user: User | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type CampaignStatus = "ACTIVE" | "PAUSED" | "ARCHIVED";

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  status: CampaignStatus;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
  link_count: number;
  total_visits: number;
  unique_visitors: number;
}

export interface UtmParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

export interface Link {
  id: string;
  campaign_id: string | null;
  campaign_name: string | null;
  campaign_status: CampaignStatus | null;
  short_code: string;
  short_url: string;
  target_url: string;
  description: string | null;
  tags: string[] | null;
  is_active: boolean;
  expires_at: string | null;
  is_password_protected: boolean;
  requires_consent: boolean;
  utm_params: UtmParams | null;
  created_at: string;
  updated_at: string;
  total_visits: number;
  unique_visitors: number;
}

export type TriState = "YES" | "NO" | "UNKNOWN";

export interface Visit {
  id: string;
  created_at: string;
  consent_given: boolean;
  ip_address: string | null;
  country: string | null;
  country_code: string | null;
  region: string | null;
  city: string | null;
  district: string | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  isp: string | null;
  asn: string | null;
  organization: string | null;
  hostname: string | null;
  is_mobile: boolean | null;
  device_type: string | null;
  browser: string | null;
  browser_version: string | null;
  os: string | null;
  os_version: string | null;
  language: string | null;
  referrer: string | null;
  is_vpn: TriState;
  is_proxy: TriState;
  is_tor: TriState;
  is_hosting: TriState;
  bot_confidence: string;
  utm_snapshot: Record<string, string> | null;
  visit_number: number | null;
  is_returning_visitor: boolean;
}

export interface DashboardSummary {
  total_links: number;
  total_visits: number;
  unique_visitors: number;
  today_visits: number;
  active_campaigns: number;
  conversion_rate: number;
}

export interface TopItem {
  label: string;
  count: number;
}

export interface TimeseriesPoint {
  date: string;
  count: number;
}

export type DateRangePreset = "today" | "yesterday" | "7d" | "30d" | "90d";

export interface Session {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_used_at: string;
  expires_at: string;
  is_current: boolean;
}

// --- Analytics ---------------------------------------------------------------

export interface AnalyticsOverview {
  total_visits: number;
  unique_visitors: number;
  conversion_rate: number;
  timeseries: TimeseriesPoint[];
  top_countries: TopItem[];
  top_devices: TopItem[];
  top_browsers: TopItem[];
  top_os: TopItem[];
  top_referrers: TopItem[];
}

// --- URL Tools -----------------------------------------------------------------

export interface UrlAnalysisResult {
  final_url: string;
  status_code: number;
  redirect_count: number;
  elapsed_ms: number;
  content_type: string | null;
  title: string | null;
  description: string | null;
  favicon_url: string | null;
}

export interface RedirectHop {
  url: string;
  status_code: number;
  location: string | null;
  elapsed_ms: number;
}

export interface RedirectCheckResult {
  hops: RedirectHop[];
  final_url: string;
  final_status_code: number;
}

// --- Security Center -----------------------------------------------------------

export interface SslInfo {
  valid: boolean;
  issuer?: string | null;
  subject?: string | null;
  expires_at?: string | null;
  days_remaining?: number | null;
  protocol?: string | null;
  cipher?: string | null;
}

export interface HeadersInfo {
  reachable: boolean;
  status_code?: number;
  error?: string;
  headers: Record<string, string | null>;
}

export interface WhoisInfo {
  registrar: string | null;
  creation_date: string | null;
  expiration_date: string | null;
  name_servers: string[];
  status: string[];
}

export interface ReputationInfo {
  verdict: "clean" | "suspicious" | "malicious";
  categories: string[];
  provider: string;
}

export interface DomainIpInfo {
  ip_address: string;
  country: string | null;
  country_code: string | null;
  region: string | null;
  city: string | null;
  isp: string | null;
  asn: string | null;
  organization: string | null;
  hostname: string | null;
  is_hosting: TriState;
  provider: string;
}

export interface DnsPropagationInfo {
  resolvers: Record<string, string[]>;
  consistent: boolean;
}

export interface CookieFinding {
  name: string;
  secure: boolean;
  http_only: boolean;
  same_site: string | null;
  issues: string[];
}

export interface TechFinding {
  category: string;
  technology: string;
  detected_via: "header" | "cookie" | "body";
}

export interface RobotsInfo {
  robots_found: boolean;
  disallow_rules: string[];
  sitemap_found: boolean;
  sitemap_url: string | null;
  sitemap_url_count: number | null;
}

export type FindingSeverity = "high" | "medium" | "low" | "info";

export interface SecurityFinding {
  severity: FindingSeverity;
  code: string;
  params: Record<string, string | number>;
}

export interface SecurityScan {
  id: string;
  domain: string;
  score: number;
  ssl_info: SslInfo | null;
  dns_records: Record<string, string[]> | null;
  whois_info: WhoisInfo | null;
  headers_info: HeadersInfo | null;
  reputation_info: ReputationInfo | null;
  ip_info: DomainIpInfo | null;
  subdomains: string[] | null;
  dns_propagation: DnsPropagationInfo | null;
  cookie_info: CookieFinding[] | null;
  tech_info: TechFinding[] | null;
  robots_info: RobotsInfo | null;
  findings: SecurityFinding[] | null;
  created_at: string;
}

// --- API keys ------------------------------------------------------------------

export type ApiKeyTier = "FREE" | "PRO" | "BUSINESS";

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  tier: ApiKeyTier;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
  revoked_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  api_key: string;
}

// --- Webhooks ------------------------------------------------------------------

export type WebhookEventType = "link.created" | "link.clicked" | "campaign.created" | "campaign.completed" | "security.alert";

export interface Webhook {
  id: string;
  url: string;
  description: string | null;
  events: string[];
  is_active: boolean;
  secret_preview: string;
  created_at: string;
  updated_at: string;
}

export interface WebhookCreated extends Webhook {
  secret: string;
}

export type WebhookDeliveryStatus = "PENDING" | "SUCCESS" | "FAILED";

export interface WebhookDelivery {
  id: string;
  event_type: string;
  status: WebhookDeliveryStatus;
  response_status_code: number | null;
  attempt_count: number;
  next_retry_at: string | null;
  delivered_at: string | null;
  created_at: string;
}

// --- Notifications ---------------------------------------------------------

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

// --- Devices (remote control) ---------------------------------------------

export interface Device {
  id: string;
  name: string;
  platform: string;
  is_active: boolean;
  last_seen_at: string | null;
  paired_at: string;
  revoked_at: string | null;
  created_at: string;
}

export interface PairingCodeCreated {
  code: string;
  expires_at: string;
  qr_code_data_url: string;
}

export interface IceServer {
  urls: string;
  username?: string | null;
  credential?: string | null;
}

export type DeviceSessionStatus = "PENDING" | "ACTIVE" | "ENDED" | "EXPIRED";

export interface DeviceSession {
  id: string;
  status: DeviceSessionStatus;
  started_at: string | null;
  ended_at: string | null;
  ended_reason: string | null;
  expires_at: string;
  created_at: string;
}

export interface DeviceSessionStart {
  session_id: string;
  web_ticket: string;
  ice_servers: IceServer[];
  expires_at: string;
}

// Signaling WS envelope — must stay in sync with backend/app/api/v1/devices.py
// and docs/DEVICE_CONTROL_PROTOCOL.md.
export type SignalMessage =
  | { type: "offer"; data: RTCSessionDescriptionInit }
  | { type: "answer"; data: RTCSessionDescriptionInit }
  | { type: "ice-candidate"; data: RTCIceCandidateInit }
  | { type: "bye"; data: { reason?: string } };

// RTCDataChannel("input") message shape — normalized 0..1 pointer
// coordinates so it's independent of either peer's actual resolution.
export type DeviceInputMessage =
  | { type: "pointer"; action: "down" | "move" | "up"; x: number; y: number }
  | { type: "key"; action: "down" | "up"; key: string; code: string };
