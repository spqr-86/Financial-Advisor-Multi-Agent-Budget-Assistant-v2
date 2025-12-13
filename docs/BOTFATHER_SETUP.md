# BotFather Configuration Guide

This guide explains how to configure your Telegram bot using BotFather to enable the Persistent Menu and update command descriptions.

## Prerequisites

- Telegram account
- Bot created via @BotFather
- Bot token (already configured in `.env`)

## Step 1: Set Bot Commands

Commands appear in the `/` menu and provide autocomplete suggestions to users.

1. Open Telegram and find **@BotFather**
2. Send `/setcommands`
3. Select your bot from the list
4. Send the following commands list:

```
start - Начать работу с ботом
help - Помощь и примеры использования
add - Добавить расход (пошагово)
stats - Показать статистику
last - Показать последние расходы
delete - Удалить последний расход
examples - Примеры использования
```

5. BotFather will confirm: "Success! Command list updated."

## Step 2: Set Bot Menu Button (Persistent Menu)

The persistent menu appears as a button next to the message input field.

1. In @BotFather, send `/setmenubutton`
2. Select your bot from the list
3. Choose "Edit menu button"
4. Send the following menu structure:

```
💰 Добавить - /add
📊 Статистика - /stats
📝 Последние - /last
❓ Помощь - /help
```

**Note:** The Persistent Menu in Telegram Bot API currently supports a single button that opens a web app or shows commands. For Budget Assistant, we recommend using the standard commands menu (/start, /help, /add, etc.) which is automatically available to users.

**Alternative (Web App approach - not implemented yet):**
If you want a custom menu with multiple buttons, you would need to implement a Telegram Mini App (Web App), which is beyond the scope of Phase 2.

## Step 3: Set Bot Description

This appears when users first start a chat with your bot.

1. In @BotFather, send `/setdescription`
2. Select your bot
3. Send:

```
👋 Привет! Я Budget Assistant v2.0 - твой личный помощник по финансам.

🎯 Что я умею:
• Записываю расходы в Google Sheets
• Автоматически определяю категории
• Показываю статистику и аналитику
• Даю советы по экономии

📝 Попробуй написать:
"купил хлеб 50 рублей"

или используй команды:
/add - Добавить расход пошагово
/stats - Статистика
/help - Помощь
```

## Step 4: Set Short Description

This appears in the bot's profile and search results.

1. In @BotFather, send `/setabouttext`
2. Select your bot
3. Send:

```
AI-помощник для учета личных финансов. Записывает расходы в Google Sheets и показывает статистику.
```

## Step 5: Set Bot Profile Photo (Optional)

1. In @BotFather, send `/setuserpic`
2. Select your bot
3. Upload an image (512x512 pixels recommended)

Suggested image: 💰 emoji or a custom logo with money/finance theme

## Verification

After setup, test your bot:

1. Open your bot in Telegram
2. Click the `/` button - you should see all commands
3. Type `/add` - the structured expense flow should start
4. Commands should autocomplete as you type

## Current Limitation: Persistent Menu

Telegram's Bot API persistent menu is limited to:
- A single "Menu" button that can:
  - Open a web app (requires Mini App development)
  - Show default commands (what we currently use)

**For Phase 2, we rely on:**
- **Command menu** (`/` button) with all bot commands
- **Inline keyboards** (buttons attached to messages)
- **Reply keyboards** (shown during `/add` flow)

This provides excellent UX without requiring a Web App implementation.

## Future Enhancement: Mini App

For a true persistent menu with multiple buttons, you would need to:
1. Create a Telegram Mini App (HTML/JS/CSS web interface)
2. Host it on a public URL
3. Configure it via BotFather's `/newapp` command
4. Update menu button to launch the app

This is beyond the scope of Phase 2 but could be considered for future iterations.

## Troubleshooting

**Commands not showing:**
- Make sure you sent the exact format to BotFather
- Restart your Telegram app
- Clear chat history with the bot and send `/start` again

**Descriptions not updating:**
- Wait a few minutes for Telegram servers to sync
- Clear cache or reinstall Telegram app

**Menu button not working:**
- Telegram's default menu button shows commands - this is expected
- Custom menu requires Web App (not implemented)

## Resources

- [Telegram Bot API - Commands](https://core.telegram.org/bots/features#commands)
- [Telegram Bot API - Menu Button](https://core.telegram.org/bots/features#menu-button)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
