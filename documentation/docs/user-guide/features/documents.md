# Document Collaboration

Native Colab's document module provides real-time collaborative editing, version control, and document management for your team.

## Overview

Document features include:
- **Real-Time Collaboration**: Multiple users editing simultaneously
- **Rich Text Editor**: Full formatting capabilities
- **Version History**: Track changes and restore previous versions
- **Commenting**: Discuss and suggest changes
- **Templates**: Standardized document formats
- **Sharing & Permissions**: Control access levels
- **Export Options**: PDF, DOCX, Markdown
- **Folder Organization**: Keep documents organized

## Creating Documents

### New Document

1. Click **Documents** in sidebar
2. Click **"New Document"**
3. Choose document type:
   - Blank document
   - From template
   - Import existing file
4. Name your document
5. Start editing

### Document from Template

Use pre-built templates:
- Meeting Notes
- Project Proposal
- Technical Specification
- Requirements Document
- Release Notes
- Weekly Report

1. Click **"New from Template"**
2. Browse templates
3. Select template
4. Customize and save

### Importing Documents

Import existing documents:

1. Click **"Import"**
2. Select file type:
   - Microsoft Word (.docx)
   - PDF (.pdf)
   - Markdown (.md)
   - Plain Text (.txt)
3. Upload file
4. Document converts automatically

## The Editor

### Toolbar

**Text Formatting:**
- Bold, Italic, Underline, Strikethrough
- Font size and color
- Highlight color
- Clear formatting

**Paragraphs:**
- Headings (H1-H6)
- Bulleted lists
- Numbered lists
- Checklists
- Block quotes
- Code blocks

**Insert:**
- Images
- Links
- Tables
- Horizontal rules
- Emojis
- Mentions

**Alignment:**
- Left
- Center
- Right
- Justify

### Formatting Options

#### Headings
```
# Heading 1
## Heading 2
### Heading 3
```
Or use the heading dropdown

#### Lists

**Bulleted:**
- Type `-` or `*` followed by space
- Or click bullet list button

**Numbered:**
1. Type `1.` followed by space
2. Or click numbered list button

**Checklists:**
- [ ] Type `[]` for checkbox
- [x] Click to check/uncheck

#### Links
1. Select text
2. Click link button
3. Enter URL
4. Or use: `[Link text](https://example.com)`

#### Images
1. Click image button
2. Upload from computer
3. Or paste image URL
4. Drag to resize

#### Tables
1. Click table button
2. Select rows and columns
3. Click to add
4. Right-click for table options

#### Code Blocks
````markdown
```javascript
const hello = "world";
```
````
Or use the code block button

### Markdown Support

The editor supports Markdown:

```markdown
**bold** or __bold__
*italic* or _italic_
~~strikethrough~~
`inline code`
[link](https://example.com)
![image](image-url.png)
> blockquote
---
- bullet list
1. numbered list
```

## Real-Time Collaboration

### Working Together

Multiple users can edit simultaneously:

- **See who's online**: Avatar icons show active editors
- **Live cursors**: See where others are typing
- **Instant updates**: Changes appear immediately
- **No conflicts**: Automatic merge of changes

### Presence Indicators

**Active Users:**
- Colored avatars in top-right
- Cursor with name badge
- Click avatar to jump to their location

**Following Users:**
- Click user's avatar
- Your view follows their cursor
- Click again to stop following

### Commenting

Add comments without editing text:

1. Select text
2. Click comment icon
3. Type comment
4. Tag users with `@username`
5. Click **"Comment"**

**Managing Comments:**
- Reply to comments
- Resolve when addressed
- Reopen if needed
- View resolved comments

### Suggesting Changes

Suggestion mode for non-destructive edits:

1. Click **"Suggesting"** mode
2. Make changes
3. Changes highlighted in color
4. Document owner accepts/rejects

## Document Organization

### Folders

Organize documents in folders:

1. Click **"New Folder"**
2. Name folder
3. Drag documents to folder
4. Create nested folders

**Folder Actions:**
- Rename
- Move
- Share (shares all contents)
- Delete

### Favorites

Star important documents:
1. Hover over document
2. Click star icon
3. Access from **"Favorites"** filter

### Recent Documents

Quickly access recent work:
- Automatically tracked
- Shows last 20 documents
- Click **"Recent"** to view

### Search

Find documents quickly:

1. Click search box
2. Enter keywords
3. Filter by:
   - Modified date
   - Created by
   - File type
   - Folder location

## Sharing & Permissions

### Share Document

1. Click **"Share"** button
2. Choose sharing method:
   - Invite specific users
   - Generate shareable link
   - Share to channel

### Permission Levels

**Owner**
- Full control
- Delete document
- Change permissions
- Transfer ownership

**Editor**
- Edit content
- Add comments
- Invite others (if allowed)

**Commenter**
- Add comments
- View content
- Cannot edit

**Viewer**
- View only
- No edits or comments
- Can download (if allowed)

### Link Sharing

**Generate Link:**
1. Click **"Get Link"**
2. Choose access level:
   - Anyone with link (public)
   - Workspace members only
   - Specific people only
3. Set permissions (view/comment/edit)
4. Set expiration date (optional)
5. Copy link

**Link Options:**
- Require sign-in
- Disable downloads
- Password protection
- Expiration date

### Guest Access

Share with external users:
1. Click **"Share"**
2. Enter external email
3. Set permission level
4. They receive email invitation
5. Guest account created automatically

## Version History

### Viewing History

1. Click **"Version History"**
2. Timeline of changes appears
3. Click any version to preview
4. See who made changes

### Restoring Versions

1. Open version history
2. Find version to restore
3. Click **"Restore"**
4. Confirm restoration
5. Current version saved as new version

### Version Naming

Name important versions:
1. View version history
2. Hover over version
3. Click **"Name Version"**
4. Enter descriptive name (e.g., "Final Draft")
5. Save

### Comparing Versions

1. Open version history
2. Select two versions
3. Click **"Compare"**
4. See highlighted differences:
   - Green: Added content
   - Red: Removed content
   - Yellow: Modified content

## Document Templates

### Creating Templates

Save documents as templates:

1. Create and format document
2. Click **More** → **"Save as Template"**
3. Name template
4. Add description
5. Set category
6. Save

### Managing Templates

1. Go to **Settings** → **Templates**
2. View all templates
3. Edit template content
4. Set permissions
5. Archive unused templates

### Template Variables

Use variables for dynamic content:

```
{{author.name}}
{{current.date}}
{{project.name}}
{{workspace.name}}
```

Variables auto-fill when template is used.

## Exporting Documents

### Export Formats

Export to various formats:
- **PDF**: For sharing and printing
- **Microsoft Word (.docx)**: For external editing
- **Markdown (.md)**: For developers
- **Plain Text (.txt)**: Basic format
- **HTML**: Web-ready format

### Export Process

1. Click **"Export"**
2. Select format
3. Choose options:
   - Include comments
   - Include version history
   - Page size (for PDF)
   - Formatting options
4. Click **"Download"**

### Bulk Export

Export multiple documents:
1. Select documents (checkbox)
2. Click **"Export Selected"**
3. Choose format
4. Downloads as ZIP file

## Document Settings

### Page Settings

Configure page layout:
- **Paper Size**: Letter, A4, Legal
- **Orientation**: Portrait, Landscape
- **Margins**: Normal, Narrow, Wide, Custom
- **Line Spacing**: Single, 1.5, Double

### Document Properties

Set metadata:
- Title
- Author
- Created date
- Tags
- Custom fields

### Access Logs

View document activity:
- Who viewed
- Who edited
- When accessed
- Changes made

Access logs available to document owners.

## Advanced Features

### Table of Contents

Auto-generate TOC:
1. Click **"Insert"** → **"Table of Contents"**
2. TOC created from headings
3. Updates automatically
4. Click entries to jump

### Cross-References

Link to other documents:
1. Type `@` or click mention button
2. Search for document
3. Select document
4. Link inserted

### Bookmarks

Add bookmarks to long documents:
1. Select location
2. Click **"Insert"** → **"Bookmark"**
3. Name bookmark
4. Use for internal navigation

### Document Locking

Prevent concurrent edits:
1. Click **"Lock Document"**
2. Only you can edit
3. Others see read-only view
4. Unlock when finished

## Best Practices

### Writing & Formatting

1. **Consistent Formatting**: Use styles, not manual formatting
2. **Clear Headings**: Organize with heading hierarchy
3. **Short Paragraphs**: Easier to read and scan
4. **Use Lists**: Break down complex information
5. **Add Context**: Link to related documents

### Collaboration

1. **Comments Over Edits**: Use comments for suggestions
2. **@Mention Reviewers**: Tag specific people
3. **Resolve Comments**: Mark as resolved when addressed
4. **Version Milestones**: Name important versions
5. **Clear Ownership**: Define document owner

### Organization

1. **Folder Structure**: Organize by project/team
2. **Naming Convention**: Descriptive, consistent names
3. **Archive Old Docs**: Keep workspace clean
4. **Use Tags**: For cross-project documents
5. **Templates**: Standardize common document types

### Security

1. **Review Permissions**: Regularly audit access
2. **Link Expiration**: Set expiry on shared links
3. **Download Control**: Disable if sensitive
4. **Version Control**: Don't delete important versions
5. **Backup**: Export critical documents

## Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|--------------|-----|
| Bold | `Ctrl + B` | `Cmd + B` |
| Italic | `Ctrl + I` | `Cmd + I` |
| Underline | `Ctrl + U` | `Cmd + U` |
| Link | `Ctrl + K` | `Cmd + K` |
| Save | `Ctrl + S` | `Cmd + S` |
| Find | `Ctrl + F` | `Cmd + F` |
| Undo | `Ctrl + Z` | `Cmd + Z` |
| Redo | `Ctrl + Y` | `Cmd + Shift + Z` |
| Comment | `Ctrl + Alt + M` | `Cmd + Opt + M` |

## Troubleshooting

### Changes Not Saving?
- Check internet connection
- Look for sync status icon
- Force refresh (Ctrl+Shift+R)
- Check browser console for errors

### Collaboration Issues?
- Ensure all users on same version
- Check firewall settings
- Clear browser cache
- Try different browser

### Export Failed?
- Check document size (max 50MB)
- Try different format
- Remove large images
- Contact support

## Next Steps

- [Learn about Digital Signatures →](./digital-signatures)
- [Explore Time Tracking →](./time-tracking)
- [Document Collaboration Guide →](../guides/collaborating-documents)
