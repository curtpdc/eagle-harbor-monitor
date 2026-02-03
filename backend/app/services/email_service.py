from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config import settings


class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.FROM_EMAIL
    
    async def send_verification_email(self, to_email: str, token: str):
        """Send email verification link"""
        
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
        
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(to_email),
            subject="Verify Your Email - Eagle Harbor Monitor",
            html_content=Content("text/html", html_content)
        )
        
        try:
            self.sg.send(message)
        except Exception as e:
            print(f"Error sending verification email: {e}")
            raise
    
    async def send_welcome_email(self, to_email: str, unsubscribe_token: str):
        """Send welcome email after verification"""
        
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
        
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(to_email),
            subject="Welcome to Eagle Harbor Data Center Monitor!",
            html_content=Content("text/html", html_content)
        )
        
        try:
            self.sg.send(message)
        except Exception as e:
            print(f"Error sending welcome email: {e}")
    
    async def send_instant_alert(self, subscribers: list, article: dict):
        """Send instant alert for high-priority articles"""
        
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
        
        # Send to all subscribers (batch in production)
        for subscriber_email in subscribers[:100]:  # Limit for SendGrid free tier
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(subscriber_email),
                subject=f"🚨 URGENT: {article['title'][:60]}...",
                html_content=Content("text/html", html_content)
            )
            
            try:
                self.sg.send(message)
            except Exception as e:
                print(f"Error sending alert to {subscriber_email}: {e}")
