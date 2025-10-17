# Google Drive OAuth Setup Instructions

## Problem

Service accounts cannot upload files to personal Google Drive folders due to storage quota limitations. The solution is to use OAuth 2.0, which allows the app to access your Drive using your personal storage quota.

## Setup Steps

### 1. Create OAuth 2.0 Credentials

1. Go to: https://console.cloud.google.com/apis/credentials
2. Make sure your project "microcapagent" is selected at the top
3. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**

### 2. Configure OAuth Consent Screen (if prompted)

If you're prompted to configure the consent screen first:

1. Click **"CONFIGURE CONSENT SCREEN"**
2. Choose **"External"** (for personal Gmail accounts)
3. Click **"CREATE"**
4. Fill in required fields:
   - **App name**: `MicroCap Monitoring Agent`
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **"SAVE AND CONTINUE"**
6. On "Scopes" page, click **"SAVE AND CONTINUE"** (we'll add scopes in code)
7. On "Test users" page, click **"+ ADD USERS"**
8. Add your Gmail address
9. Click **"SAVE AND CONTINUE"**
10. Review and click **"BACK TO DASHBOARD"**

### 3. Create OAuth Client ID

1. Go back to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `MicroCap Agent Desktop`
5. Click **"CREATE"**

### 4. Download Credentials

1. A dialog will appear with your Client ID and Client Secret
2. Click **"DOWNLOAD JSON"**
3. Save the file to your project folder as:
   ```
   ~/microcap_agent/google_oauth_credentials.json
   ```

### 5. Test OAuth Upload

Run the test script:

```bash
cd ~/microcap_agent
python google_drive_oauth.py
```

**What will happen:**
1. A browser window will open
2. You'll see a Google sign-in page
3. Sign in with your Gmail account
4. You'll see a warning "Google hasn't verified this app"
   - Click **"Advanced"**
   - Click **"Go to MicroCap Monitoring Agent (unsafe)"**
5. Click **"Allow"** to grant Drive access
6. The browser will show "The authentication flow has completed"
7. Close the browser and return to terminal
8. The test will upload a file to your Drive

### 6. Update Monitoring Agent

The monitoring agent needs to be updated to use OAuth instead of service account.

---

## Benefits of OAuth vs Service Account

✓ **Works with personal Gmail** - No Google Workspace required
✓ **Uses your storage quota** - No quota limitations
✓ **One-time authorization** - Token saved and refreshed automatically
✓ **More secure** - User explicitly authorizes access

## Files Created

- `google_oauth_credentials.json` - OAuth client credentials (add to .gitignore)
- `token.pickle` - Saved user token (add to .gitignore)
- Both files should NOT be committed to git

---

## Troubleshooting

**"Access blocked: Authorization Error"**
- Make sure you added yourself as a test user in OAuth consent screen

**"redirect_uri_mismatch"**
- The OAuth client type should be "Desktop app", not "Web application"

**Browser doesn't open**
- Check firewall settings
- Try running from a different terminal
