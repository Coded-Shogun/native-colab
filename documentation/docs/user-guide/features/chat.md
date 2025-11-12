# Chat & Messaging

Native Colab's chat feature provides real-time communication with your team through channels, direct messages, and threads.

## Overview

The chat module supports:
- **Public & Private Channels**: Organized team conversations
- **Direct Messages**: 1-on-1 and group DMs
- **Threads**: Organized sub-conversations
- **File Sharing**: Share files, images, and documents
- **Reactions**: React to messages with emojis
- **Mentions**: Tag team members and channels
- **Rich Formatting**: Markdown support for messages
- **Search**: Find messages across all conversations

## Channels

### Creating a Channel

1. Click the **+** icon next to **Channels** in the sidebar
2. Choose channel type:
   - **Public Channel**: Visible to all workspace members
   - **Private Channel**: Invite-only
3. Fill in channel details:
   ```
   Channel Name: #marketing-team
   Description: Marketing team discussions
   Privacy: Public/Private
   ```
4. Add members (for private channels)
5. Click **"Create Channel"**

### Channel Naming Best Practices

- Use lowercase with hyphens: `#product-launch`
- Keep it descriptive: `#bug-reports` not `#misc`
- Use prefixes for organization:
  - `#team-*` for team channels
  - `#project-*` for project-specific channels
  - `#social-*` for casual conversations

### Channel Settings

Access channel settings by clicking the channel name:

- **Description**: Update channel purpose
- **Members**: Add or remove members
- **Notifications**: Configure alert settings
- **Pinned Messages**: Pin important messages
- **Archive**: Archive inactive channels

### Joining & Leaving Channels

**Join a Channel:**
1. Click **Browse Channels**
2. Find the channel you want to join
3. Click **"Join"**

**Leave a Channel:**
1. Right-click the channel name
2. Select **"Leave Channel"**
3. Confirm

## Direct Messages

### Starting a Direct Message

1. Click the **+** icon next to **Direct Messages**
2. Search for team members
3. Select one or more members:
   - **One member**: 1-on-1 conversation
   - **Multiple members**: Group DM
4. Start messaging

### Group Direct Messages

- Add up to 20 participants
- Name the group (optional)
- Group persists until all members leave
- Cannot convert to a channel (create new channel instead)

## Sending Messages

### Basic Messaging

Type your message and press **Enter** to send.

**Tips:**
- Press **Shift + Enter** for a new line without sending
- Press **↑** to edit your last message
- Type `/` to see available commands

### Message Formatting

Native Colab supports Markdown:

```markdown
**bold text**
*italic text*
~~strikethrough~~
`inline code`
```code block```
> quote
- bullet list
1. numbered list
[link text](https://example.com)
```

### Mentions

**Mention a User:**
Type `@username` to notify a specific person

**Mention Everyone:**
Type `@channel` to notify all channel members (use sparingly!)

**Mention Here:**
Type `@here` to notify only online members

### File Sharing

**Upload Files:**
1. Click the paperclip icon or drag-and-drop
2. Select files (images, documents, videos)
3. Add optional message
4. Send

**Supported File Types:**
- Images: JPG, PNG, GIF, SVG
- Documents: PDF, DOCX, XLSX, PPTX
- Archives: ZIP, RAR
- Code: TXT, JSON, XML, etc.
- Max size: 100MB per file

### Code Snippets

Share formatted code:

1. Click the code icon **</>**
2. Select language
3. Paste your code
4. Add description (optional)
5. Send

Or use inline code blocks:
````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

### Emojis & Reactions

**Add Emoji to Message:**
- Click emoji picker icon
- Or type `:emoji_name:` (e.g., `:smile:`, `:rocket:`)

**React to Message:**
1. Hover over any message
2. Click the emoji reaction icon
3. Select emoji
4. Or click existing reaction to add yours

## Message Threads

Keep conversations organized with threads:

1. Hover over a message
2. Click **"Reply in thread"**
3. Type your reply
4. Thread appears in the right sidebar

**Benefits:**
- Keeps channels clean
- Focused discussions
- Easy to follow conversations
- Notifications for thread participants

## Message Actions

Hover over any message to see actions:

- **React**: Add emoji reaction
- **Thread**: Reply in thread
- **Share**: Share to another channel
- **Pin**: Pin important messages
- **Edit**: Edit your own messages
- **Delete**: Delete your own messages
- **Copy Link**: Get permanent link to message
- **Mark Unread**: Mark as unread to revisit later

## Search

### Global Search

Press `Ctrl/Cmd + K` and search for:
- Messages by content
- Messages by sender
- Messages in specific channels
- Messages with files

### Advanced Filters

Use search operators:
```
from:@username          # Messages from specific user
in:#channel-name        # Messages in specific channel
has:link                # Messages with links
has:file                # Messages with attachments
before:2024-01-01       # Messages before date
after:2024-01-01        # Messages after date
```

## Notifications

### Configuring Notifications

1. Go to **Settings** → **Notifications**
2. Choose notification triggers:
   - Direct messages
   - Mentions
   - Keywords
   - All messages (in specific channels)
3. Select notification method:
   - Desktop notifications
   - Email
   - Mobile push
   - Sound

### Do Not Disturb

Enable DND to pause notifications:

1. Click your profile icon
2. Select **"Do Not Disturb"**
3. Choose duration:
   - 30 minutes
   - 1 hour
   - 2 hours
   - Until tomorrow
   - Custom

### Custom Notification Sounds

1. Go to **Settings** → **Notifications** → **Sounds**
2. Upload custom sound file
3. Assign to different notification types

## Status & Presence

### Setting Your Status

1. Click your profile icon
2. Select status:
   - 🟢 **Active**: Available
   - 🟡 **Away**: Temporarily unavailable
   - 🔴 **Busy**: Do not disturb
   - ⚫ **Offline**: Not available
3. Add custom status message (optional)
4. Set clear time (optional)

### Custom Status Messages

Examples:
- "In a meeting until 3 PM"
- "Working remotely"
- "On vacation 🏖️"
- "Focusing - limited availability"

## Keyboard Shortcuts

Essential chat shortcuts:

| Action | Windows/Linux | Mac |
|--------|--------------|-----|
| Quick switcher | `Ctrl + K` | `Cmd + K` |
| Mark all as read | `Shift + Esc` | `Shift + Esc` |
| Previous channel | `Alt + ↑` | `Opt + ↑` |
| Next channel | `Alt + ↓` | `Opt + ↓` |
| Edit last message | `↑` | `↑` |
| Search | `Ctrl + F` | `Cmd + F` |
| Upload file | `Ctrl + U` | `Cmd + U` |

View all shortcuts: Press `Ctrl/Cmd + /`

## Best Practices

### Channel Organization

1. **Create Purpose-Specific Channels**: Avoid catch-all channels
2. **Set Clear Descriptions**: Help members understand channel purpose
3. **Regular Cleanup**: Archive inactive channels
4. **Pin Important Info**: Use pinned messages for guidelines

### Communication Etiquette

1. **Use Threads**: Keep conversations organized
2. **Be Considerate**: Use @channel sparingly
3. **Stay On Topic**: Use appropriate channels
4. **Professional Tone**: Maintain workplace professionalism
5. **Respect DND**: Check status before urgent mentions

### Effective Messaging

1. **Be Clear**: State purpose upfront
2. **Use Formatting**: Make messages scannable
3. **Break Up Long Messages**: Use threads for detailed discussions
4. **Respond Promptly**: Acknowledge messages within reasonable time
5. **Use Reactions**: Quick acknowledgment with emoji

## Advanced Features

### Message Reminders

Set reminders for messages:

1. Hover over message
2. Click **More** → **Remind me**
3. Choose time:
   - In 1 hour
   - Tomorrow
   - Next week
   - Custom

### Saved Messages

Save important messages:

1. Hover over message
2. Click **Save**
3. Access saved messages from sidebar

### Voice Messages

Record audio messages:

1. Click microphone icon
2. Hold to record
3. Release to send
4. Slide left to cancel

## Troubleshooting

### Messages Not Sending?
- Check internet connection
- Refresh the page
- Check message length (max 10,000 characters)

### Can't See New Messages?
- Click channel to mark as read
- Check notification settings
- Ensure you're added to the channel

### File Upload Failed?
- Check file size (max 100MB)
- Verify file type is supported
- Check storage quota

## Tips & Tricks

- **Multi-line Messages**: Hold `Shift` while pressing `Enter`
- **Quote Reply**: Select text and click reply to quote
- **Unread Badge**: Click workspace name to mark all as read
- **Channel Sidebar**: Pin frequently used channels to top
- **Mute Channels**: Mute busy channels to reduce notifications

## Next Steps

- [Explore Projects →](./projects)
- [Try Document Collaboration →](./documents)
- [Learn About Video Calls →](./video-calls)
