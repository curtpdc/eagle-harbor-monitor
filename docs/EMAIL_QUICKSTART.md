# Email & Subscription Management - Quick Reference

## ✅ What Changed

### Replaced SendGrid → Azure Communication Services Email

**Why?**
- 50% cheaper ($10 vs $20 for 40,000 emails)
- Already in your Azure subscription
- No daily sending limits (pay-per-use)
- curtis.prince@xigusa.com sender address (after domain setup)

### New Subscriber Management Tool

Simple CLI for managing subscriptions without database queries.

---

## 🚀 Quick Setup (5 Minutes)

### 1. Get Connection String

```bash
az communication list-key \
  --name xigusa-comm \
  --resource-group rg-xigusa-ai \
  --query primaryConnectionString \
  --output tsv
```

Copy the output (looks like: `endpoint=https://...;accesskey=...`)

### 2. Update backend/.env

```bash
# Remove this line:
# SENDGRID_API_KEY=...

# Add this:
AZURE_COMM_CONNECTION_STRING="endpoint=https://xigusa-comm.unitedstates.communication.azure.com/;accesskey=YOUR_KEY_HERE"

# For now, use Azure-managed domain (instant setup):
FROM_EMAIL="DoNotReply@<guid>.azurecomm.net"

# OR after DNS verification (24-48 hours):
FROM_EMAIL="curtis.prince@xigusa.com"
```

### 3. Install Dependencies

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Test Email

```bash
cd backend
python

>>> from azure.communication.email import EmailClient
>>> client = EmailClient.from_connection_string("YOUR_CONNECTION_STRING")
>>> message = {
...     "senderAddress": "DoNotReply@xxx.azurecomm.net",
...     "recipients": {"to": [{"address": "curtis.prince@xigusa.com"}]},
...     "content": {
...         "subject": "Test Email",
...         "html": "<h1>It works!</h1>"
...     }
... }
>>> poller = client.begin_send(message)
>>> result = poller.result()
>>> print(f"Sent! ID: {result['id']}")
```

✅ **Done!** Your email system is ready.

---

## 📧 Managing Subscribers

### List All Subscribers

```bash
python manage_subscribers.py list
```

Output:
```
================================================================================
SUBSCRIBERS (3 total)
================================================================================

Email                                    Status       Joined      
---------------------------------------- ------------ ------------
curtis.prince@xigusa.com                 ✓ Verified   2026-02-04  
jane.doe@example.com                     ⏳ Pending    2026-02-03  
```

### Show Subscriber Details

```bash
python manage_subscribers.py show curtis.prince@xigusa.com
```

Output:
```
================================================================================
SUBSCRIBER DETAILS: curtis.prince@xigusa.com
================================================================================

Email:              curtis.prince@xigusa.com
Verified:           ✓ Yes
Created:            2026-02-04 10:30:15
Verification Token: a1b2c3d4e5f6g7h8i9j0...
Unsubscribe Token:  k1l2m3n4o5p6q7r8s9t0...

Total Alerts Sent:  12
```

### Manually Verify Subscriber

Bypass email verification (useful for testing):

```bash
python manage_subscribers.py verify curtis.prince@xigusa.com
```

### Delete Subscriber

```bash
python manage_subscribers.py delete test@example.com
```

Prompts for confirmation before deleting.

### Show Statistics

```bash
python manage_subscribers.py stats
```

Output:
```
================================================================================
EAGLE HARBOR MONITOR - STATISTICS
================================================================================

SUBSCRIBERS
  Total:           15
  ✓ Verified:      12
  ⏳ Pending:       3
  Newest:          jane.doe@example.com (2026-02-04)

CONTENT
  Articles:        25
  Analyzed:        25
  High Priority:   5 (score ≥ 7)

ALERTS
  Sent:            12
```

---

## 🔧 Using Custom Domain (curtis.prince@xigusa.com)

### Option 1: Quick Start (Azure-Managed Domain)

**Use this for immediate testing:**
- FROM_EMAIL will be: `DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`
- ✅ Works instantly, no DNS setup
- ❌ Generic sender address

### Option 2: Production (Custom Domain)

**Use this for professional emails from curtis.prince@xigusa.com:**

1. **Add DNS records to xigusa.com**:

```bash
# Get DNS verification records
az communication email domain show \
  --domain-name xigusa.com \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai
```

2. **Add these to your DNS provider**:
   - TXT record: `MS=ms12345678` (domain ownership)
   - SPF record: `v=spf1 include:spf.protection.outlook.com -all`
   - DKIM CNAME records (2 records shown in output)

3. **Wait 24-48 hours** for DNS propagation

4. **Update .env**:
   ```bash
   FROM_EMAIL="curtis.prince@xigusa.com"
   ```

---

## 💰 Cost Tracking

### Current Cost

With 100 subscribers:
- 1 email/day × 100 subscribers × 30 days = 3,000 emails/month
- **Cost: $0.75/month** (3,000 × $0.00025)

### Monitor in Azure Portal

1. Go to **xigusa-comm** resource
2. Click **Cost Management** → **Cost Analysis**
3. Filter by **Communication Services Email**

### Cost Comparison

| Subscribers | Emails/Month | SendGrid | Azure CS | Savings |
|------------|--------------|----------|----------|---------|
| 100        | 3,000        | $19.95   | $0.75    | 96%     |
| 500        | 15,000       | $19.95   | $3.75    | 81%     |
| 1,000      | 30,000       | $19.95   | $7.50    | 62%     |
| 2,000      | 60,000       | $79.95   | $15.00   | 81%     |

---

## 🎯 Daily Workflow

### Check Subscription Status

```bash
python manage_subscribers.py stats
```

### Manually Verify Test Subscriber

```bash
python manage_subscribers.py verify test@example.com
```

### Remove Spam/Bounced Email

```bash
python manage_subscribers.py delete spam@example.com
```

---

## ⚠️ Troubleshooting

### "Sender address not verified"

**Solution 1 (Quick)**: Use Azure-managed domain
```bash
# Get Azure-managed domain from portal or:
az communication email domain list \
  --email-service-name xigusa-comm \
  --resource-group rg-xigusa-ai
```

**Solution 2 (Production)**: Verify xigusa.com (takes 24-48 hours for DNS)

### "Connection string invalid"

Re-fetch connection string:
```bash
az communication list-key \
  --name xigusa-comm \
  --resource-group rg-xigusa-ai \
  --query primaryConnectionString
```

### Emails Going to Spam

1. Use custom domain (Option 2 above)
2. Set up SPF/DKIM/DMARC records
3. Use consistent "From" address
4. Warm up sending (start with 50/day, increase gradually)

---

## 📝 Files Modified

✅ `backend/app/services/email_service.py` - Azure Communication Services SDK
✅ `backend/app/config.py` - AZURE_COMM_CONNECTION_STRING setting
✅ `backend/requirements.txt` - azure-communication-email package
✅ `backend/manage_subscribers.py` - Subscriber management CLI tool
✅ `docs/AZURE_EMAIL_SETUP.md` - Detailed setup guide

---

## 🎉 Next Steps

1. [ ] Get Azure Communication Services connection string
2. [ ] Update `backend/.env`
3. [ ] Run `pip install -r requirements.txt`
4. [ ] Test email with Python script
5. [ ] Test subscription flow (subscribe → verify → welcome)
6. [ ] (Optional) Set up custom domain DNS for curtis.prince@xigusa.com

**Estimated setup time**: 5 minutes (Azure-managed domain) or 2-3 days (custom domain with DNS)
