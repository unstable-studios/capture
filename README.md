# Dev Config Capture

A comprehensive tool to snapshot your development environment configuration for backup, migration, or team onboarding purposes.

## What It Captures

- **Git**: Global/system config, repo-local configs
- **SSH**: Config files, public keys (NO private keys)
- **Shell**: Dotfiles (`.zshrc`, `.bashrc`, etc.) + declarative "essence" extraction
- **Oh My Zsh**: Theme, plugins, custom additions + source URLs for reinstallation
- **Plugin Managers**: Detects zinit, antigen, zplug, zgen/zgenom, prezto
- **Editors**: VS Code & Cursor settings, keybindings, snippets, extensions
- **Terminal Tools**: Tmux, Vim/Neovim configurations
- **Package Managers**: Homebrew (`Brewfile`), npm, pip, rustup, cargo
- **Toolchains**: Node, Python, Rust, Go, Terraform, Docker versions
- **Environment Managers**: asdf, nvm, pyenv, rbenv configs
- **Kubernetes**: Config (redacted)
- **macOS**: App defaults, Mac App Store apps (via `mas`)
- **GPG**: Public key listings (NO private keys)

## Quick Start

```bash
# Basic usage - creates snapshot in current directory
./capture

# Specify custom output directory
./capture ~/my-backup-2025

# Override which directories to scan for git repos
SCAN_ROOTS="$HOME/work $HOME/personal" ./capture
```

## Output Structure

```
dev-config-snapshot-20251222-143055/
├── README.md                    # Overview of snapshot
├── metadata.txt                 # Timestamp, OS, hostname, user
├── git/                         # Git configuration
│   ├── config--global.txt
│   ├── files/.gitconfig
│   └── repo-local/              # Individual repo configs
├── ssh/                         # SSH config (public only)
│   ├── config
│   └── public_keys/
├── shell/                       # Shell configuration
│   ├── raw/                     # Original dotfiles
│   ├── essence/                 # Declarative rebuild recipes
│   │   └── zshrc-essence.md
│   ├── omz/                     # Oh My Zsh metadata
│   └── sources/                 # Plugin/theme source URLs
│       ├── zsh-sources.md
│       └── git-origins.txt
├── tmux/
├── vim/ & nvim/
├── kubernetes/
├── vscode/                      # VS Code settings
│   ├── settings.json
│   ├── extensions.txt
│   └── snippets/
├── cursor/                      # Cursor editor settings
├── brew/                        # Homebrew
│   ├── Brewfile                 # ⭐ Key file for restore
│   └── brew-list.txt
├── env/                         # Environment managers
│   ├── asdf/.tool-versions
│   ├── node/.npmrc
│   └── python/pip.conf
└── docker/
```

## Restoration Workflow

### 1. Install Core Tools

```bash
# macOS: Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Restore all Homebrew packages, casks, and taps
brew bundle install --file ./brew/Brewfile

# Mac App Store apps (if mas is installed)
# Review ./macos/mas-list.txt and install manually or via mas
```

### 2. Git Configuration

```bash
# Copy global git config
cp ./git/files/.gitconfig ~/.gitconfig

# Or selectively apply settings
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
# ... etc from git/config--global.txt
```

### 3. SSH Configuration

```bash
# Copy SSH config (review first!)
cp ./ssh/config ~/.ssh/config
chmod 600 ~/.ssh/config

# Copy public keys if needed
cp ./ssh/public_keys/* ~/.ssh/
```

### 4. Shell & Oh My Zsh

```bash
# Install Oh My Zsh (if not already installed)
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Use shell/essence/zshrc-essence.md as your rebuild guide
# It contains:
# - Theme to set
# - Plugins to enable
# - PATH additions
# - Aliases
# - Environment variables

# Install custom plugins/themes from shell/sources/zsh-sources.md
# Example:
# cd ~/.oh-my-zsh/custom/plugins
# git clone https://github.com/zsh-users/zsh-autosuggestions
```

### 5. VS Code / Cursor

```bash
# Install VS Code extensions
cat ./vscode/extensions.txt | xargs -L 1 code --install-extension

# Install Cursor extensions
cat ./cursor/extensions.txt | xargs -L 1 cursor --install-extension

# Copy settings
cp ./vscode/settings.json ~/Library/Application\ Support/Code/User/
cp ./vscode/keybindings.json ~/Library/Application\ Support/Code/User/
cp -r ./vscode/snippets ~/Library/Application\ Support/Code/User/

# Similar for Cursor
```

### 6. Other Tools

```bash
# Tmux
cp ./tmux/.tmux.conf ~/.tmux.conf

# Vim
cp ./vim/.vimrc ~/.vimrc
cp -r ./vim/.vim ~/

# Neovim
cp -r ./nvim ~/.config/

# Kubernetes (review redactions!)
cp ./kubernetes/config ~/.kube/config
chmod 600 ~/.kube/config
```

### 7. Environment Setup

```bash
# asdf
cp ./env/asdf/.tool-versions ~/
asdf install

# Node/npm
cp ./env/node/.npmrc ~/
# Install global packages from env/node/npm-global.txt

# Python
pip3 install -r ./env/python/pip3-freeze.txt
```

## Security & Privacy

### ⚠️ Important Warnings

1. **Review before sharing** - While the script includes redaction, it's not foolproof
2. **Snapshots contain sensitive data** - Treat them like you would SSH keys
3. **Add to `.gitignore`** - Never commit snapshots to public repos
4. **Check output manually** - Inspect generated files before sharing

### What's Redacted

The script attempts to redact:

- Bearer tokens (`Authorization: Bearer ...`)
- API keys (`api_key=...`, `token=...`)
- Passwords (`password=...`)
- AWS access keys (`AKIA...`)
- Private keys (PEM format)
- Various `*_SECRET`, `*_TOKEN`, `*_PASSWORD` environment variables

### What's NOT Captured

- SSH private keys
- GPG private keys
- Browser data
- Application passwords/tokens not in config files
- Encrypted credentials (e.g., macOS Keychain)

## Advanced Usage

### Custom Scan Directories

```bash
# Override which directories to scan for repo-local git configs
SCAN_ROOTS="/path/to/projects /another/path" ./capture
```

### Scheduling Backups

```bash
# Add to crontab for weekly snapshots
# Run every Sunday at 2 AM
0 2 * * 0 /path/to/capture ~/backups/config-$(date +\%Y\%m\%d)
```

### Comparing Snapshots

```bash
# See what changed between two snapshots
diff -r snapshot-old/ snapshot-new/ > differences.txt

# Compare specific configs
diff snapshot-old/shell/essence/zshrc-essence.md \
     snapshot-new/shell/essence/zshrc-essence.md
```

## Troubleshooting

### "Permission denied" errors

- Normal - the script continues on errors
- Check the tool is installed and accessible

### Missing tools

- Install missing tools via Homebrew or system package manager
- Script skips sections for missing commands

### Redaction not working

- Requires `perl` to be installed (usually pre-installed on macOS/Linux)
- Check output files manually if concerned

### Large output directory

- The script can generate 10-50MB depending on your setup
- Most space is from Homebrew listings and tool inventories

## Contributing

Suggestions for improvement:

- Additional configs to capture
- Better redaction patterns
- Cross-platform compatibility improvements
- Restore automation scripts

## License

MIT License - See LICENSE file

## Related Tools

- [mackup](https://github.com/lra/mackup) - Application settings sync
- [homesick](https://github.com/technicalpickles/homesick) - Dotfiles management
- [dotbot](https://github.com/anishathalye/dotbot) - Dotfiles installer
- [chezmoi](https://github.com/twpayne/chezmoi) - Dotfiles manager with templating

## Why This Tool?

Unlike other dotfile managers:

- **One-time snapshot** rather than continuous sync
- **Forensic approach** - captures _everything_ then helps you rebuild declaratively
- **Migration-focused** - designed for setting up new machines or helping teammates
- **No lock-in** - generates standard formats (Brewfile, extension lists, etc.)
