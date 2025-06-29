# 🔐 Google Account Integration Setup Guide

This comprehensive guide will help you set up Google account authentication for TailorTalk Enhanced, allowing testers to use their own Google accounts securely.

## 📋 Prerequisites

- Google account with access to Google Cloud Console
- Python 3.8+ installed
- TailorTalk Enhanced application files

## 🚀 Step-by-Step Setup

### Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select Project**
   \`\`\`
   - Click "Select a project" dropdown
   - Click "New Project"
   - Enter project name: "TailorTalk Enhanced"
   - Click "Create"
   \`\`\`

3. **Enable Required APIs**
   \`\`\`
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"
   - Search for "Google People API" (optional)
   - Click on it and press "Enable"
   \`\`\`

### Step 2: OAuth 2.0 Credentials

1. **Create OAuth 2.0 Client ID**
   \`\`\`
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Name: "TailorTalk Enhanced Desktop"
   - Click "Create"
   \`\`\`

2. **Download Credentials**
   \`\`\`
   - Click the download button (⬇️) next to your client ID
   - Save the file as "credentials.json"
   - Place it in the "config/" directory of TailorTalk
   \`\`\`

### Step 3: OAuth Consent Screen Configuration

1. **Configure Consent Screen**
   \`\`\`
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Click "Create"
   \`\`\`

2. **Fill App Information**
   \`\`\`
   App name: TailorTalk Enhanced
   User support email: your-email@example.com
   App logo: (optional)
   App domain: localhost (for testing)
   Developer contact: your-email@example.com
   \`\`\`

3. **Add Scopes**
   \`\`\`
   Click "Add or Remove Scopes" and add:
   - https://www.googleapis.com/auth/calendar
   - https://www.googleapis.com/auth/userinfo.email
   - https://www.googleapis.com/auth/userinfo.profile
   \`\`\`

4. **Add Test Users**
   \`\`\`
   - Add email addresses of people who will test the app
   - Include your own email and any tester emails
   - Save and continue
   \`\`\`

### Step 4: Application Configuration

1. **Run Setup Script**
   \`\`\`bash
   cd tailortalk-enhanced
   python config/setup_google_credentials.py
   \`\`\`

2. **Verify Credentials File**
   \`\`\`
   config/
   └── credentials.json  ← Should exist here
   \`\`\`

3. **Set Environment Variables**
   \`\`\`bash
   # Create .env file
   cp .env.sample .env
   
   # Edit .env file
   GOOGLE_CREDENTIALS_PATH=config/credentials.json
   TIMEZONE=Asia/Kolkata
   DEBUG=true
   \`\`\`

### Step 5: Security Configuration

1. **Update OAuth Client Settings**
   \`\`\`
   - Go back to Google Cloud Console
   - Edit your OAuth 2.0 client
   - Add authorized redirect URIs:
     * http://localhost:8001/auth/callback
     * http://127.0.0.1:8001/auth/callback
   \`\`\`

2. **Configure Application URLs**
   \`\`\`
   - Authorized JavaScript origins:
     * http://localhost:8501 (Streamlit)
     * http://localhost:8001 (FastAPI)
   \`\`\`

## 🧪 Testing the Setup

### 1. Start the Application

\`\`\`bash
# Start FastAPI backend
python start_enhanced.py

# In another terminal, start Streamlit
streamlit run enhanced_streamlit_app.py --server.port 8501
\`\`\`

### 2. Test Authentication Flow

1. **Open Streamlit App**
   - Go to: http://localhost:8501
   - You should see the TailorTalk interface

2. **Authenticate with Google**
   - Click "Authenticate with Google" button
   - You'll be redirected to Google's OAuth page
   - Sign in with a test user account
   - Grant permissions to TailorTalk

3. **Verify Integration**
   - After authentication, you should see user info in sidebar
   - Click "Test Calendar Access" to verify permissions
   - Try booking an appointment

### 3. Test API Endpoints

\`\`\`bash
# Check authentication status
curl http://localhost:8001/auth/status/your-user-id

# List authenticated users
curl http://localhost:8001/auth/users

# Test calendar access
curl http://localhost:8001/auth/test/your-user-id
\`\`\`

## 🔒 Security Best Practices

### For Development

1. **Credential Security**
   \`\`\`
   - Never commit credentials.json to version control
   - Add config/credentials.json to .gitignore
   - Use environment variables for sensitive data
   \`\`\`

2. **User Data Protection**
   \`\`\`
   - All credentials are encrypted at rest
   - Sessions expire after 24 hours
   - Users can revoke access anytime
   \`\`\`

3. **API Rate Limits**
   \`\`\`
   - Implement proper rate limiting
   - Cache calendar data when possible
   - Handle API quota exceeded errors
   \`\`\`

### For Production

1. **Use Web Application Type**
   \`\`\`
   - Create new OAuth client for production
   - Use "Web application" type instead of "Desktop"
   - Configure proper redirect URIs for your domain
   \`\`\`

2. **Environment Variables**
   \`\`\`bash
   export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   export SECRET_KEY=your-production-secret-key
   export ENCRYPTION_KEY=your-production-encryption-key
   \`\`\`

3. **Domain Verification**
   \`\`\`
   - Verify your domain in Google Cloud Console
   - Update OAuth consent screen with production domain
   - Remove localhost URLs from authorized origins
   \`\`\`

## 🛠️ Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" Error**
   \`\`\`
   Solution:
   - Check OAuth client redirect URIs in Google Cloud Console
   - Ensure http://localhost:8001/auth/callback is added
   - Verify the port matches your FastAPI server
   \`\`\`

2. **"access_denied" Error**
   \`\`\`
   Solution:
   - Check if user is added to test users list
   - Verify OAuth consent screen is configured
   - Ensure required scopes are added
   \`\`\`

3. **"invalid_client" Error**
   \`\`\`
   Solution:
   - Verify credentials.json file is valid
   - Check if client ID and secret are correct
   - Ensure OAuth client is enabled
   \`\`\`

4. **Calendar API Errors**
   \`\`\`
   Solution:
   - Verify Google Calendar API is enabled
   - Check if user has granted calendar permissions
   - Ensure calendar scope is included in OAuth request
   \`\`\`

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
# In your .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Or set environment variable
export DEBUG=true
