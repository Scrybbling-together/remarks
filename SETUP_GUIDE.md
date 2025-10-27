# ReMarkable to Markdown Converter - Setup Guide

This guide covers how to set up and run the remarks converter using either:
1. Local installation (with setup script)
2. Docker container

## Prerequisites

### For Local Installation
- Python 3.12 or higher
- macOS: Homebrew installed
- Linux: apt-get or yum package manager

### For Docker Installation
- Docker installed
- Docker Compose (optional, for easier usage)

## Quick Start

### Option 1: Local Installation

1. **Clone the repository** (after forking):
   ```bash
   git clone git@github.com:YOUR_USERNAME/remarks.git
   cd remarks
   ```

2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

4. **Convert your files**:
   ```bash
   python -m remarks /path/to/remarkable-backup/xochitl /path/to/output
   ```

### Option 2: Docker Installation

#### Using docker-compose (Recommended)

1. **Clone the repository** (after forking):
   ```bash
   git clone git@github.com:YOUR_USERNAME/remarks.git
   cd remarks
   ```

2. **Set environment variables**:
   ```bash
   export INPUT_DIR=/path/to/remarkable-backup/xochitl
   export OUTPUT_DIR=/path/to/output
   ```

3. **Run with docker-compose**:
   ```bash
   docker-compose up
   ```

#### Using Docker directly

1. **Build the Docker image**:
   ```bash
   docker build -t remarks:latest .
   ```

2. **Run the converter**:
   ```bash
   docker run --rm \
     -v /path/to/remarkable-backup/xochitl:/input:ro \
     -v /path/to/output:/output \
     remarks:latest /input /output
   ```

## Usage Examples

### Convert with specific log level
```bash
# Local
python -m remarks ~/remarkable-backup/xochitl ~/output --log_level DEBUG

# Docker
docker run --rm \
  -v ~/remarkable-backup/xochitl:/input:ro \
  -v ~/output:/output \
  remarks:latest /input /output --log_level DEBUG
```

### Convert a single .rmn or .rmdoc file
```bash
# Local
python -m remarks ~/Documents/my-notebook.rmn ~/output

# Docker
docker run --rm \
  -v ~/Documents/my-notebook.rmn:/input.rmn:ro \
  -v ~/output:/output \
  remarks:latest /input.rmn /output
```

## Output Files

The converter generates two types of files:

1. **`*_obsidian.md`** - Markdown files with:
   - YAML frontmatter (metadata, tags)
   - Extracted text content
   - Highlights from PDFs
   - Formatted content (bold, italic, headings, bullets, checkboxes)

2. **`*_remarks.pdf`** - Annotated PDFs with:
   - Original document content
   - ReMarkable annotations overlaid
   - Handwritten notes rendered

## Required Input Files

For each document, you need:
- `*.metadata` - Document metadata
- `*.content` - Document structure
- `*.rm` - ReMarkable annotation files (v6 format)
- Source PDF/EPUB (if annotating existing documents)

## Troubleshooting

### "Cairo library not found"
- **macOS**: Run `brew install cairo`
- **Linux**: Run `apt-get install libcairo2-dev` or `yum install cairo-devel`

### "No .metadata files found"
Ensure you're pointing to the correct xochitl directory from your ReMarkable backup.

### Permission denied errors
Ensure output directory has write permissions:
```bash
chmod 755 /path/to/output
```

### Docker volume mounting issues
Use absolute paths for volume mounts, not relative paths.

## Advanced Configuration

### Using .env file with docker-compose

Create a `.env` file in the project root:
```bash
INPUT_DIR=/Users/you/remarkable-backup/xochitl
OUTPUT_DIR=/Users/you/remarkable-output
LOG_LEVEL=INFO
```

Then run:
```bash
docker-compose up
```

### Building for different architectures

For ARM64 (Apple Silicon):
```bash
docker buildx build --platform linux/arm64 -t remarks:arm64 .
```

For AMD64:
```bash
docker buildx build --platform linux/amd64 -t remarks:amd64 .
```

## Forking the Repository

Since this is not your repository, you should fork it first:

1. Go to https://github.com/Scrybbling-together/remarks
2. Click "Fork" in the top right
3. Clone your fork:
   ```bash
   git clone git@github.com:YOUR_USERNAME/remarks.git
   ```
4. Add these new files to your fork
5. Commit and push:
   ```bash
   git add setup.sh Dockerfile docker-compose.yml SETUP_GUIDE.md
   git commit -m "Add setup script and Docker support"
   git push origin main
   ```

## Credits

- Original remarks project: https://github.com/Scrybbling-together/remarks
- Scrybble service: https://scrybble.ink

## License

This project inherits the GPL-3.0 license from the original remarks project.
