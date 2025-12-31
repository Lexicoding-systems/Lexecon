# Lexecon Wiki Content

This directory contains the wiki pages for the Lexecon repository.

## Wiki Pages

- **Home.md** - Main wiki landing page with navigation
- **Installation.md** - Installation instructions for various platforms
- **Getting-Started.md** - Quick start guide and tutorial
- **Architecture.md** - System architecture and design
- **API-Reference.md** - REST API and Python SDK documentation
- **Policy-Guide.md** - Guide to writing and managing policies
- **FAQ.md** - Frequently asked questions
- **Troubleshooting.md** - Common issues and solutions

## How to Upload to GitHub Wiki

GitHub wikis are stored in a separate `.wiki` git repository. Follow these steps to upload the wiki content:

### Method 1: Clone and Push to Wiki Repository

1. **Enable Wiki** on your GitHub repository:
   - Go to your repository on GitHub
   - Click "Settings"
   - Scroll down to "Features"
   - Check "Wikis"

2. **Clone the wiki repository**:
   ```bash
   git clone https://github.com/Lexicoding-systems/Lexecon.wiki.git
   cd Lexecon.wiki
   ```

3. **Copy wiki files** from this directory:
   ```bash
   cp /path/to/Lexecon/wiki/*.md .
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add wiki content"
   git push origin master
   ```

### Method 2: Manual Upload via GitHub UI

1. **Go to the Wiki tab** in your repository on GitHub

2. **Create each page manually**:
   - Click "Create the first page" or "New Page"
   - For the home page, use the title "Home"
   - Copy content from `Home.md`
   - Click "Save Page"

3. **Repeat for other pages**:
   - Click "New Page"
   - Use the filename without `.md` as the title (e.g., "Installation")
   - Copy content from the corresponding `.md` file
   - Save each page

4. **Note**: GitHub Wiki uses the page title as the filename, converting spaces to hyphens

### Method 3: Use GitHub CLI

If you have the GitHub CLI installed:

```bash
# Navigate to wiki repository
git clone https://github.com/Lexicoding-systems/Lexecon.wiki.git
cd Lexecon.wiki

# Copy files
cp /path/to/Lexecon/wiki/*.md .

# Commit and push
git add .
git commit -m "Initialize wiki"
git push
```

## Wiki File Naming Convention

GitHub wiki converts page titles to filenames:
- "Home" → `Home.md`
- "Getting Started" → `Getting-Started.md`
- "API Reference" → `API-Reference.md`

The files in this directory already follow this convention.

## Internal Links

The wiki pages use the `[[Page Name]]` syntax for internal links, which GitHub automatically converts to proper wiki links.

For example:
- `[[Installation]]` links to the Installation page
- `[[Getting Started]]` links to the Getting Started page
- `[[API Reference]]` links to the API Reference page

## Updating the Wiki

To update the wiki:

1. Clone the wiki repository
2. Make changes to the `.md` files
3. Commit and push the changes
4. The wiki will be updated immediately

## Wiki vs Regular Documentation

This wiki complements the regular documentation:

- **README.md**: Quick overview and getting started
- **docs/**: Detailed technical documentation
- **wiki/**: User-friendly guides and references

The wiki is designed to be:
- More accessible for beginners
- Better organized for different audiences
- Easier to navigate and search
- Community-editable (if enabled)

## Contributing to the Wiki

To contribute:

1. Fork the main repository
2. Update files in the `wiki/` directory
3. Submit a pull request
4. Once merged, the wiki maintainer will update the GitHub wiki

## License

All wiki content is licensed under the same MIT License as the main project.
