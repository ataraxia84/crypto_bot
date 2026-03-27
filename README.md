# Telegram Crypto Price Bot

A GitHub Actions bot that sends cryptocurrency price updates to Telegram every 8 hours with 1h, 24h, and 7d percentage changes.

## Features

- ✅ Automatic price updates every 8 hours
- ✅ Price changes: 1 hour, 24 hours, 7 days
- ✅ Support for multiple cryptocurrencies
- ✅ Manual trigger option
- ✅ Error notifications
- ✅ Color-coded percentage changes (🟢 for gains, 🔴 for losses)

## Setup Instructions

### 1. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Save the **bot token** you receive (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Start a chat with your bot by searching for its username and clicking "Start"
5. Get your **chat ID**:
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789}` in the response

### 2. Add Secrets to GitHub Repository

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

| Secret Name | Value |
|------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID (numeric) |
| `CRYPTO_COINS` | (Optional) Custom coin list: `bitcoin,ethereum,solana` |

### 3. Enable GitHub Actions

The workflow will automatically run:
- Every 8 hours at 00:00, 08:00, 16:00 UTC
- Manually via **Actions** tab → **Telegram Crypto Price Bot** → **Run workflow**

### 4. Test Your Bot

1. Go to **Actions** tab in your repository
2. Select "Telegram Crypto Price Bot" workflow
3. Click **Run workflow** → **Run workflow** button
4. Check your Telegram for the price update

## Customization

### Change Update Frequency

Edit `.github/workflows/telegram-bot.yml` and modify the cron schedule:
```yaml
schedule:
  - cron: '0 */8 * * *'  # Every 8 hours
  # Other examples:
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 9,17,1 * * *'  # Specific times: 9am, 5pm, 1am
