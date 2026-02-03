# API Keys - Quick Setup Guide

## 1. Anthropic API Key (Required for AI Analysis)

**Get your key:**
1. Visit https://console.anthropic.com
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

**Pricing:**
- Pay-as-you-go
- Claude Sonnet 4.5: $3 per million input tokens, $15 per million output tokens
- Estimated: $50-100/month for this application

## 2. SendGrid API Key (Required for Email Notifications)

**Get your key:**
1. Visit https://signup.sendgrid.com (free tier available)
2. Sign up with your email
3. Verify your email address
4. Go to Settings → API Keys
5. Create API Key with "Full Access"
6. Copy the key (starts with `SG.`)

**Free Tier:**
- 100 emails per day forever free
- Perfect for initial testing
- Upgrade to 40,000 emails/month for $15/month when needed

## Quick Start (Optional - Skip for Now)

You can deploy without API keys initially to test the infrastructure:
- Backend API will work
- Article storage will work
- AI analysis and email will be disabled until you add keys later

## Adding Keys Later

Update environment variables in Azure:

```powershell
# Update Backend
az webapp config appsettings set `
    --resource-group xigusa-webapp `
    --name eagle-harbor-api `
    --settings ANTHROPIC_API_KEY="your-key" SENDGRID_API_KEY="your-key"

# Update Functions
az functionapp config appsettings set `
    --resource-group xigusa-webapp `
    --name eagle-harbor-functions `
    --settings ANTHROPIC_API_KEY="your-key"

# Restart apps
az webapp restart --resource-group xigusa-webapp --name eagle-harbor-api
az functionapp restart --resource-group xigusa-webapp --name eagle-harbor-functions
```

## Domain Email Setup (SendGrid)

To send from alerts@eagleharbormonitor.org:
1. Purchase domain or use existing
2. In SendGrid: Settings → Sender Authentication
3. Authenticate your domain
4. Add DNS records provided by SendGrid
5. Update FROM_EMAIL in app settings

For testing, you can use your verified email address.
