# Azure Communication Services Email Setup Guide

## Why Azure Communication Services Email?

**Cost Comparison:**
- **SendGrid Free**: 100 emails/day, then $19.95/month for 40,000 emails
- **Azure Communication Services**: $0.00025/email = **$10/month for 40,000 emails** (50% cheaper!)
- ✅ **Already in your Azure subscription** - no new vendor needed

## Setup Steps

### 1. Get Your Connection String

You have Azure Communication Services at: `https://xigusa-comm.unitedstates.communication.azure.com`

```bash
# Get your connection string (run this in Azure CLI)
az communication list-key \
  --name xigusa-comm \
  --resource-group rg-xigusa-ai \
  --query primaryConnectionString \
  --output tsv
```

### 2. Configure Email Domain

Azure Communication Services requires domain verification. You have two options:

#### Option A: Use Azure-Managed Domain (Quick Start - Recommended)
Azure provides a free managed domain for testing:

```bash
# Check available Azure-managed domains
az communication email domain list \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai
```

The sender email will be something like: `DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`

**Pros**: 
- ✅ Instant setup (no DNS configuration)
- ✅ Free
- ✅ Works immediately

**Cons**:
- ❌ Generic sender address (not curtis.prince@xigusa.com)
- ❌ May have lower deliverability

#### Option B: Verify Custom Domain xigusa.com (Production - Best)
Use your own domain for professional emails from curtis.prince@xigusa.com

```bash
# Create email domain resource
az communication email domain create \
  --domain-name xigusa.com \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai \
  --domain-management CustomerManaged

# Get DNS verification records
az communication email domain show \
  --domain-name xigusa.com \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai
```

You'll need to add these DNS records to xigusa.com:
- **TXT record**: For domain ownership verification
- **SPF record**: `v=spf1 include:spf.protection.outlook.com -all`
- **DKIM records**: Two CNAME records for email authentication

**After adding DNS records**, verify the domain:

```bash
az communication email domain update \
  --domain-name xigusa.com \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai
```

DNS propagation takes 24-48 hours.

### 3. Update Backend Configuration

Update `backend/.env`:

```bash
# Remove SendGrid
# SENDGRID_API_KEY=...  # DELETE THIS LINE

# Add Azure Communication Services
AZURE_COMM_CONNECTION_STRING="endpoint=https://xigusa-comm.unitedstates.communication.azure.com/;accesskey=YOUR_KEY_HERE"

# Update sender email
# Option A (Azure-managed domain):
FROM_EMAIL="DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net"

# Option B (Custom domain - after DNS verification):
FROM_EMAIL="curtis.prince@xigusa.com"
```

### 4. Install New Dependencies

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs `azure-communication-email==1.0.0` and removes `sendgrid`.

### 5. Test Email Sending

```bash
cd backend
python
```

```python
from azure.communication.email import EmailClient

# Replace with your actual connection string
conn_str = "endpoint=https://xigusa-comm.unitedstates.communication.azure.com/;accesskey=YOUR_KEY"
client = EmailClient.from_connection_string(conn_str)

# Test email
message = {
    "senderAddress": "curtis.prince@xigusa.com",  # Or Azure-managed domain
    "recipients": {
        "to": [{"address": "curtis.prince@xigusa.com"}]
    },
    "content": {
        "subject": "Test from Eagle Harbor Monitor",
        "html": "<h1>It works!</h1><p>Azure Communication Services is configured correctly.</p>"
    }
}

poller = client.begin_send(message)
result = poller.result()
print(f"Email sent! Message ID: {result['id']}")
```

## Subscriber Management

Simple CLI tool for managing subscriptions:

```bash
cd backend

# List all subscribers
python manage_subscribers.py list

# Show subscriber details
python manage_subscribers.py show curtis.prince@xigusa.com

# Manually verify a subscriber (bypass email verification)
python manage_subscribers.py verify curtis.prince@xigusa.com

# Delete a subscriber
python manage_subscribers.py delete test@example.com

# Show statistics
python manage_subscribers.py stats
```

### Example Output:

```
================================================================================
SUBSCRIBERS (3 total)
================================================================================

Email                                    Status       Joined      
---------------------------------------- ------------ ------------
curtis.prince@xigusa.com                 ✓ Verified   2026-02-04  
jane.doe@example.com                     ⏳ Pending    2026-02-03  
john.smith@example.com                   ✓ Verified   2026-02-02  
```

## Email Deliverability Tips

1. **Use Custom Domain (xigusa.com)** for better deliverability
2. **SPF/DKIM/DMARC**: Set up all three for production
3. **Monitor Bounce Rate**: Azure portal shows email metrics
4. **Start Small**: Test with 10-20 subscribers first
5. **Warm Up**: Gradually increase email volume (50/day → 100/day → 500/day)

## Cost Monitoring

Track costs in Azure Portal:
1. Navigate to **xigusa-comm** resource
2. Click **Cost Management** → **Cost Analysis**
3. Filter by **Communication Services Email**

**Expected costs** (with 100 subscribers):
- 1 email/day × 100 subscribers × 30 days = 3,000 emails/month
- Cost: 3,000 × $0.00025 = **$0.75/month**
- Compare to SendGrid Free: 100 emails/day limit would be exceeded

## Troubleshooting

### "Sender address not verified"
- **Option A**: Use Azure-managed domain from step 2
- **Option B**: Complete DNS verification for xigusa.com (takes 24-48 hours)

### "Connection string invalid"
```bash
# Re-fetch connection string
az communication list-key \
  --name xigusa-comm \
  --resource-group rg-xigusa-ai \
  --query primaryConnectionString
```

### Emails going to spam
- Set up SPF/DKIM/DMARC records (Option B above)
- Use consistent "From" address
- Avoid spam trigger words in subject lines
- Include unsubscribe link (already in templates)

## Migration Checklist

- [ ] Get Azure Communication Services connection string
- [ ] Choose domain option (Azure-managed vs custom domain)
- [ ] Update `backend/.env` with connection string
- [ ] Update `FROM_EMAIL` in `.env`
- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Test email sending with test script
- [ ] Test subscriber flow: subscribe → verify → welcome email
- [ ] Monitor Azure portal for email delivery metrics
- [ ] (Optional) Add DNS records for custom domain

## Next Steps

After email setup works:
1. Test full subscription flow (subscribe → verify → alerts)
2. Use `manage_subscribers.py` for simple management
3. Consider adding web admin panel if subscriber count grows
4. Set up email bounce handling (Azure Event Grid webhooks)
