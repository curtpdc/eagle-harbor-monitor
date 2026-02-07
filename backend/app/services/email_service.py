from azure.communication.email import EmailClient
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Azure Communication Services Email client (optional for local dev)
        if settings.AZURE_COMM_CONNECTION_STRING:
            self.client = EmailClient.from_connection_string(settings.AZURE_COMM_CONNECTION_STRING)
            self.from_email = settings.FROM_EMAIL
            self.enabled = True
        else:
            self.client = None
            self.from_email = settings.FROM_EMAIL
            self.enabled = False
            logger.warning("Email service disabled: AZURE_COMM_CONNECTION_STRING not configured")
    
    async def send_verification_email(self, to_email: str, token: str):
        """Send email verification link"""
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would send verification email to {to_email} with token {token}")
            logger.info(f"[DEV MODE] Verification URL: {settings.APP_URL}/verify/{token}")
            return
        
        verify_url = f"{settings.APP_URL}/verify/{token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1e40af; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">Eagle Harbor Data Center Monitor</h1>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2>Verify Your Email</h2>
                <p>Thank you for subscribing to the Eagle Harbor Data Center Monitor!</p>
                <p>Click the button below to verify your email address and start receiving alerts:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{verify_url}">{verify_url}</a>
                </p>
            </div>
            
            <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                <p>If you didn't request this, you can safely ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        message = {
            "senderAddress": self.from_email,
            "recipients": {
                "to": [{"address": to_email}]
            },
            "content": {
                "subject": "Verify Your Email - Eagle Harbor Monitor",
                "html": html_content
            }
        }
        
        try:
            poller = self.client.begin_send(message)
            result = poller.result()
            print(f"Verification email sent to {to_email}. Message ID: {result['id']}")
        except Exception as e:
            print(f"Error sending verification email: {e}")
            raise
    
    async def send_welcome_email(self, to_email: str, unsubscribe_token: str):
        """Send welcome email after verification"""
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would send welcome email to {to_email}")
            logger.info(f"[DEV MODE] Unsubscribe URL: {settings.APP_URL}/unsubscribe/{unsubscribe_token}")
            return
        
        unsubscribe_url = f"{settings.APP_URL}/unsubscribe/{unsubscribe_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #10b981; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">✅ You're All Set!</h1>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2>Welcome to Eagle Harbor Data Center Monitor</h2>
                <p>You're now subscribed to receive alerts about data center developments in Prince George's County and Charles County, Maryland.</p>
                
                <h3>What to Expect:</h3>
                <ul>
                    <li>🚨 <strong>Instant Alerts</strong> for critical policy changes and votes</li>
                    <li>📊 <strong>Weekly Digest</strong> every Friday at 3 PM</li>
                    <li>📰 <strong>News Updates</strong> from government meetings and local sources</li>
                    <li>🌍 <strong>Environmental Data</strong> tracking air quality and infrastructure</li>
                </ul>
                
                <h3>Stay Informed:</h3>
                <p>Visit our website anytime to:</p>
                <ul>
                    <li>Browse recent articles and alerts</li>
                    <li>Ask questions about data center policy</li>
                    <li>View environmental monitoring data</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL}" 
                       style="background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Visit Website
                    </a>
                </div>
            </div>
            
            <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                <p>
                    <a href="{unsubscribe_url}" style="color: #6b7280;">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        message = {
            "senderAddress": self.from_email,
            "recipients": {
                "to": [{"address": to_email}]
            },
            "content": {
                "subject": "Welcome to Eagle Harbor Data Center Monitor!",
                "html": html_content
            }
        }
        
        try:
            poller = self.client.begin_send(message)
            result = poller.result()
            print(f"Welcome email sent to {to_email}. Message ID: {result['id']}")
        except Exception as e:
            print(f"Error sending welcome email: {e}")
    
    async def send_instant_alert(self, subscribers: list, article: dict):
        """Send instant alert for high-priority articles"""
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would send instant alert to {len(subscribers)} subscribers")
            logger.info(f"[DEV MODE] Article: {article.get('title', 'Unknown title')}")
            return
        
        # Get first subscriber's unsubscribe token for template
        # In production, personalize per subscriber
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">🚨 URGENT ALERT</h1>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2>{article['title']}</h2>
                
                <p style="color: #6b7280;">
                    <strong>Source:</strong> {article['source']}<br>
                    <strong>Date:</strong> {article.get('published_date', 'Unknown')}<br>
                    <strong>Priority:</strong> <span style="color: #dc3545;">HIGH</span>
                </p>
                
                <div style="background: white; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <h3>Summary</h3>
                    <p>{article.get('summary', 'No summary available')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{article['url']}" 
                       style="background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Read Full Article
                    </a>
                </div>
            </div>
            
            <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                <p>You're receiving this because you subscribed to Eagle Harbor Data Center Monitor</p>
                <p><a href="{settings.APP_URL}/unsubscribe/{{unsubscribe_token}}" style="color: #6b7280;">Unsubscribe</a></p>
            </div>
        </body>
        </html>
        """
        
        # Send to all subscribers
        # Azure Communication Services has no daily limit (pay per use)
        for subscriber_email in subscribers:
            message = {
                "senderAddress": self.from_email,
                "recipients": {
                    "to": [{"address": subscriber_email}]
                },
                "content": {
                    "subject": f"🚨 URGENT: {article['title'][:60]}...",
                    "html": html_content
                }
            }
            
            try:
                poller = self.client.begin_send(message)
                result = poller.result()
                print(f"Alert sent to {subscriber_email}. Message ID: {result['id']}")
            except Exception as e:
                print(f"Error sending alert to {subscriber_email}: {e}")

    # ── Amendment Watchlist Alerts ────────────────────────────────────────────

    async def send_watchlist_alert(self, subscribers: list, matter_title: str,
                                    change_type: str, change_detail: str,
                                    matter_url: str = ""):
        """Send alert when a watched matter has a significant change.

        Args:
            subscribers: list of email addresses
            matter_title: e.g. "Zoning Text Amendment CZ-2026-001"
            change_type: 'status_change' | 'new_attachment' | 'vote'
            change_detail: Human-readable description of the change
            matter_url: Link to Legistar detail page
        """
        if not self.enabled:
            logger.info(
                f"[DEV MODE] Would send watchlist alert to {len(subscribers)} subscribers: "
                f"{change_type} for '{matter_title}'"
            )
            return

        type_labels = {
            "status_change": ("📋 Status Update", "#f59e0b"),
            "new_attachment": ("📎 New Document", "#3b82f6"),
            "vote": ("🗳️ Vote Recorded", "#ef4444"),
        }
        label, color = type_labels.get(change_type, ("🔔 Update", "#6b7280"))

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{label}</h1>
                <p style="margin: 5px 0 0;">Amendment Watchlist Alert</p>
            </div>

            <div style="padding: 30px; background: #f9fafb;">
                <h2>{matter_title}</h2>

                <div style="background: white; padding: 20px; border-left: 4px solid {color}; margin: 20px 0;">
                    <p style="margin: 0;">{change_detail}</p>
                </div>

                {"<div style='text-align: center; margin: 30px 0;'><a href='" + matter_url + "' style='background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;'>View on Legistar</a></div>" if matter_url else ""}

                <p style="color: #6b7280; font-size: 14px;">
                    This matter is on your watchlist. Visit <a href="{settings.APP_URL}">{settings.APP_URL}</a>
                    for full tracking details.
                </p>
            </div>

            <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                <p>Eagle Harbor Data Center Monitor — Amendment Watchlist</p>
            </div>
        </body>
        </html>
        """

        subject = f"{label}: {matter_title[:80]}"

        for subscriber_email in subscribers:
            message = {
                "senderAddress": self.from_email,
                "recipients": {"to": [{"address": subscriber_email}]},
                "content": {"subject": subject, "html": html_content},
            }
            try:
                poller = self.client.begin_send(message)
                result = poller.result()
                logger.info(f"Watchlist alert sent to {subscriber_email}: {result['id']}")
            except Exception as e:
                logger.error(f"Error sending watchlist alert to {subscriber_email}: {e}")

    # ── Weekly Digest ────────────────────────────────────────────────────────

    async def send_weekly_digest(self, to_email: str, unsubscribe_token: str,
                                  articles: list, watchlist_changes: list,
                                  upcoming_events: list):
        """Send weekly digest email with articles, watchlist changes, and upcoming events.

        Args:
            to_email: Subscriber email
            unsubscribe_token: For unsubscribe link
            articles: List of dicts with title, url, summary, priority_score, category
            watchlist_changes: List of dicts with matter_title, change_type, detail
            upcoming_events: List of dicts with title, event_date, location, event_type
        """
        if not self.enabled:
            logger.info(f"[DEV MODE] Would send weekly digest to {to_email}")
            return

        unsubscribe_url = f"{settings.APP_URL}/unsubscribe/{unsubscribe_token}"
        today = datetime.now().strftime("%B %d, %Y")

        # ── Build articles section
        article_rows = ""
        for a in articles[:15]:
            priority = a.get("priority_score", 0)
            badge = "🚨" if priority >= 8 else "⚠️" if priority >= 6 else "📰"
            article_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                    {badge} <a href="{a['url']}" style="color: #1e40af;">{a['title'][:100]}</a>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {a.get('category', '')}
                </td>
            </tr>
            """

        articles_section = ""
        if articles:
            articles_section = f"""
            <h3>📰 Top Articles This Week ({len(articles)})</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead><tr>
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #d1d5db;">Article</th>
                    <th style="padding: 8px; text-align: center; border-bottom: 2px solid #d1d5db;">Category</th>
                </tr></thead>
                <tbody>{article_rows}</tbody>
            </table>
            """

        # ── Build watchlist changes section
        watchlist_section = ""
        if watchlist_changes:
            change_items = "".join(
                f"<li><strong>{c['matter_title']}</strong>: {c['detail']}</li>"
                for c in watchlist_changes
            )
            watchlist_section = f"""
            <h3>📋 Amendment Watchlist Updates</h3>
            <ul>{change_items}</ul>
            """

        # ── Build upcoming events section
        events_section = ""
        if upcoming_events:
            event_items = "".join(
                f"<li><strong>{e.get('event_date', 'TBD')}</strong> — {e['title']}"
                f"{' @ ' + e['location'] if e.get('location') else ''}</li>"
                for e in upcoming_events
            )
            events_section = f"""
            <h3>📅 Upcoming Events</h3>
            <ul>{event_items}</ul>
            """

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1e40af; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">Weekly Digest</h1>
                <p style="margin: 5px 0 0;">Eagle Harbor Data Center Monitor — {today}</p>
            </div>

            <div style="padding: 30px; background: #f9fafb;">
                {articles_section}
                {watchlist_section}
                {events_section}

                {"<p style='color: #9ca3af;'>No notable updates this week. We'll keep watching.</p>" if not articles and not watchlist_changes and not upcoming_events else ""}

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL}"
                       style="background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Visit Dashboard
                    </a>
                </div>
            </div>

            <div style="padding: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                <p>
                    <a href="{unsubscribe_url}" style="color: #6b7280;">Unsubscribe</a> |
                    <a href="{settings.APP_URL}" style="color: #6b7280;">Website</a>
                </p>
            </div>
        </body>
        </html>
        """

        message = {
            "senderAddress": self.from_email,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"Weekly Digest — Eagle Harbor Monitor ({today})",
                "html": html_content,
            },
        }

        try:
            poller = self.client.begin_send(message)
            result = poller.result()
            logger.info(f"Weekly digest sent to {to_email}: {result['id']}")
        except Exception as e:
            logger.error(f"Error sending weekly digest to {to_email}: {e}")
