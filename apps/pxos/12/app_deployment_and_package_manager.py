#!/usr/bin/env python3
"""
PXBot App Deployment & Package Manager
Tools for packaging, distributing, and managing PXBot apps
"""

import os
import json
import shutil
import zipfile
import hashlib
import tempfile
import urllib.request
from datetime import datetime
import subprocess
import sys

class AppDeploymentManager:
    def __init__(self, pxbot_instance=None):
        self.name = "App Deployment Manager"
        self.version = "1.0.0"
        self.description = "Package, deploy, and manage PXBot apps"
        self.pxbot = pxbot_instance
        
        # Deployment state
        self.packages = {}
        self.repositories = {}
        self.installed_apps = {}
        self.config = self.load_config()
        
        # Default repositories
        self.default_repos = {
            "official": "https://github.com/pxbot-official/apps",
            "community": "https://github.com/pxbot-community/apps",
            "local": os.path.join(os.getcwd(), "local_repo")
        }
        
        # Initialize
        self.scan_installed_apps()
        self.load_repositories()
    
    def load_config(self):
        """Load deployment configuration"""
        config_path = os.path.join("pxbot_code", "deployment_config.json")
        default_config = {
            "package_format": "zip",
            "auto_backup": True,
            "verify_signatures": False,
            "allow_dev_apps": True,
            "default_repo": "official",
            "package_cache_dir": os.path.join("pxbot_code", "package_cache"),
            "backup_dir": os.path.join("pxbot_code", "app_backups")
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Config load error: {e}")
        
        return default_config
    
    def save_config(self):
        """Save deployment configuration"""
        config_path = os.path.join("pxbot_code", "deployment_config.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def scan_installed_apps(self):
        """Scan for currently installed apps"""
        apps_dir = "apps"
        if not os.path.exists(apps_dir):
            return
        
        for filename in os.listdir(apps_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                app_name = filename[:-3]  # Remove .py extension
                app_path = os.path.join(apps_dir, filename)
                
                # Try to extract app metadata
                metadata = self.extract_app_metadata(app_path)
                
                self.installed_apps[app_name] = {
                    'filename': filename,
                    'path': app_path,
                    'size': os.path.getsize(app_path),
                    'modified': os.path.getmtime(app_path),
                    'metadata': metadata
                }
    
    def extract_app_metadata(self, app_path):
        """Extract metadata from app file"""
        metadata = {
            'name': 'Unknown',
            'version': '1.0.0',
            'description': 'No description',
            'author': 'Unknown',
            'dependencies': []
        }
        
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract class definition and docstring
                import ast
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Look for app class
                        if hasattr(node, 'body') and node.body:
                            for item in node.body:
                                if isinstance(item, ast.Assign):
                                    for target in item.targets:
                                        if isinstance(target, ast.Name):
                                            if target.id == 'name' and isinstance(item.value, ast.Constant):
                                                metadata['name'] = item.value.value
                                            elif target.id == 'version' and isinstance(item.value, ast.Constant):
                                                metadata['version'] = item.value.value
                                            elif target.id == 'description' and isinstance(item.value, ast.Constant):
                                                metadata['description'] = item.value.value
                
                # Extract imports for dependencies
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                metadata['dependencies'].append(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            metadata['dependencies'].append(node.module)
        
        except Exception as e:
            print(f"Error extracting metadata from {app_path}: {e}")
        
        return metadata
    
    def load_repositories(self):
        """Load repository information"""
        repos_path = os.path.join("pxbot_code", "repositories.json")
        
        try:
            if os.path.exists(repos_path):
                with open(repos_path, "r") as f:
                    self.repositories = json.load(f)
            else:
                self.repositories = self.default_repos.copy()
                self.save_repositories()
        except Exception as e:
            print(f"Error loading repositories: {e}")
            self.repositories = self.default_repos.copy()
    
    def save_repositories(self):
        """Save repository information"""
        repos_path = os.path.join("pxbot_code", "repositories.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(repos_path, "w") as f:
                json.dump(self.repositories, f, indent=2)
        except Exception as e:
            print(f"Error saving repositories: {e}")
    
    def execute_command(self, command):
        """Main command handler"""
        try:
            if command.startswith("deploy:"):
                cmd = command[7:]
                return self.handle_deployment_command(cmd)
            else:
                return "Use deploy: prefix for deployment commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_deployment_command(self, command):
        """Handle deployment-specific commands"""
        parts = command.split(":", 1)
        action = parts[0]
        
        try:
            if action == "package":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.package_app(app_name)
            
            elif action == "install":
                package_spec = parts[1] if len(parts) > 1 else ""
                return self.install_app(package_spec)
            
            elif action == "uninstall":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.uninstall_app(app_name)
            
            elif action == "update":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.update_app(app_name)
            
            elif action == "list":
                list_type = parts[1] if len(parts) > 1 else "installed"
                return self.list_apps(list_type)
            
            elif action == "search":
                query = parts[1] if len(parts) > 1 else ""
                return self.search_apps(query)
            
            elif action == "info":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.show_app_info(app_name)
            
            elif action == "repo":
                if len(parts) > 1:
                    repo_cmd = parts[1]
                    return self.handle_repository_command(repo_cmd)
                else:
                    return self.list_repositories()
            
            elif action == "backup":
                return self.backup_apps()
            
            elif action == "restore":
                backup_name = parts[1] if len(parts) > 1 else ""
                return self.restore_apps(backup_name)
            
            elif action == "validate":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.validate_app(app_name)
            
            elif action == "publish":
                app_name = parts[1] if len(parts) > 1 else ""
                return self.publish_app(app_name)
            
            elif action == "config":
                if len(parts) > 1:
                    config_cmd = parts[1]
                    return self.handle_config(config_cmd)
                else:
                    return self.show_config()
            
            elif action == "stats":
                return self.show_statistics()
            
            else:
                return self.show_help()
                
        except Exception as e:
            return f"Command error: {e}"
    
    def package_app(self, app_name):
        """Package an app for distribution"""
        if not app_name:
            return "❌ Please specify an app name to package"
        
        if app_name not in self.installed_apps:
            return f"❌ App '{app_name}' not found in installed apps"
        
        app_info = self.installed_apps[app_name]
        app_path = app_info['path']
        
        try:
            # Create package directory
            package_dir = os.path.join(self.config["package_cache_dir"], f"{app_name}_package")
            os.makedirs(package_dir, exist_ok=True)
            
            # Copy app file
            app_filename = app_info['filename']
            shutil.copy2(app_path, os.path.join(package_dir, app_filename))
            
            # Create package manifest
            manifest = {
                'name': app_info['metadata']['name'],
                'version': app_info['metadata']['version'],
                'description': app_info['metadata']['description'],
                'author': app_info['metadata'].get('author', 'Unknown'),
                'dependencies': app_info['metadata'].get('dependencies', []),
                'filename': app_filename,
                'size': app_info['size'],
                'checksum': self.calculate_checksum(app_path),
                'package_date': datetime.now().isoformat(),
                'pxbot_version': '1.0.0',  # Minimum PXBot version required
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}"
            }
            
            # Save manifest
            manifest_path = os.path.join(package_dir, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Create README if it doesn't exist
            readme_path = os.path.join(package_dir, "README.md")
            if not os.path.exists(readme_path):
                readme_content = f"""# {manifest['name']}

{manifest['description']}

## Installation

```bash
deploy:install:{app_name}
```

## Usage

```bash
{app_name.lower()}:help
```

## Version

{manifest['version']}

## Dependencies

{', '.join(manifest['dependencies']) if manifest['dependencies'] else 'None'}

## Author

{manifest['author']}
"""
                with open(readme_path, "w") as f:
                    f.write(readme_content)
            
            # Create package archive
            package_format = self.config.get("package_format", "zip")
            if package_format == "zip":
                package_path = os.path.join(self.config["package_cache_dir"], f"{app_name}_v{manifest['version']}.pxapp")
                
                with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(package_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, package_dir)
                            zipf.write(file_path, arcname)
                
                # Clean up temporary directory
                shutil.rmtree(package_dir)
                
                # Store package info
                self.packages[app_name] = {
                    'package_path': package_path,
                    'manifest': manifest,
                    'created': datetime.now().isoformat()
                }
                
                return f"📦 **Package created successfully!**\n\n**Package:** {package_path}\n**Version:** {manifest['version']}\n**Size:** {os.path.getsize(package_path)} bytes\n**Checksum:** {manifest['checksum'][:8]}..."
            
            else:
                return f"❌ Unsupported package format: {package_format}"
                
        except Exception as e:
            return f"❌ Packaging error: {e}"
    
    def install_app(self, package_spec):
        """Install an app from package or repository"""
        if not package_spec:
            return "❌ Please specify a package to install (local file, URL, or repo:appname)"
        
        try:
            # Determine installation source
            if package_spec.startswith(('http://', 'https://')):
                return self.install_from_url(package_spec)
            elif ':' in package_spec and not os.path.exists(package_spec):
                # Repository installation: repo:appname
                repo, app_name = package_spec.split(':', 1)
                return self.install_from_repository(repo, app_name)
            elif os.path.exists(package_spec):
                return self.install_from_file(package_spec)
            else:
                # Try to find in default repository
                return self.install_from_repository(self.config.get("default_repo", "official"), package_spec)
                
        except Exception as e:
            return f"❌ Installation error: {e}"
    
    def install_from_file(self, package_path):
        """Install app from local package file"""
        if not os.path.exists(package_path):
            return f"❌ Package file not found: {package_path}"
        
        try:
            # Extract package to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                if package_path.endswith('.pxapp') or package_path.endswith('.zip'):
                    with zipfile.ZipFile(package_path, 'r') as zipf:
                        zipf.extractall(temp_dir)
                else:
                    return f"❌ Unsupported package format"
                
                # Read manifest
                manifest_path = os.path.join(temp_dir, "manifest.json")
                if not os.path.exists(manifest_path):
                    return f"❌ Invalid package: missing manifest.json"
                
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                
                app_name = manifest.get('name', 'unknown')
                app_filename = manifest.get('filename', f"{app_name}.py")
                
                # Check if app already exists
                if app_name in self.installed_apps:
                    if not self.config.get("allow_dev_apps", True):
                        return f"❌ App '{app_name}' already installed"
                    
                    # Backup existing app
                    if self.config.get("auto_backup", True):
                        self.backup_single_app(app_name)
                
                # Copy app file to apps directory
                source_app = os.path.join(temp_dir, app_filename)
                target_app = os.path.join("apps", app_filename)
                
                if not os.path.exists(source_app):
                    return f"❌ App file not found in package: {app_filename}"
                
                os.makedirs("apps", exist_ok=True)
                shutil.copy2(source_app, target_app)
                
                # Verify installation
                if self.config.get("verify_signatures", False):
                    # TODO: Implement signature verification
                    pass
                
                # Update installed apps
                self.scan_installed_apps()
                
                return f"✅ **App installed successfully!**\n\n**Name:** {app_name}\n**Version:** {manifest.get('version', 'Unknown')}\n**File:** {target_app}\n**Description:** {manifest.get('description', 'No description')}"
                
        except Exception as e:
            return f"❌ Installation error: {e}"
    
    def install_from_url(self, url):
        """Install app from URL"""
        try:
            # Download package
            temp_path = os.path.join(self.config["package_cache_dir"], "temp_download.pxapp")
            os.makedirs(self.config["package_cache_dir"], exist_ok=True)
            
            urllib.request.urlretrieve(url, temp_path)
            
            # Install from downloaded file
            result = self.install_from_file(temp_path)
            
            # Clean up
            try:
                os.remove(temp_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            return f"❌ Download error: {e}"
    
    def install_from_repository(self, repo_name, app_name):
        """Install app from repository"""
        if repo_name not in self.repositories:
            return f"❌ Repository '{repo_name}' not found"
        
        repo_url = self.repositories[repo_name]
        
        # For now, simulate repository installation
        # In a real implementation, this would query the repository API
        return f"🔍 Repository installation not yet implemented.\n\nWould install '{app_name}' from '{repo_name}' repository: {repo_url}"
    
    def uninstall_app(self, app_name):
        """Uninstall an app"""
        if not app_name:
            return "❌ Please specify an app name to uninstall"
        
        if app_name not in self.installed_apps:
            return f"❌ App '{app_name}' is not installed"
        
        try:
            app_info = self.installed_apps[app_name]
            app_path = app_info['path']
            
            # Backup before uninstalling
            if self.config.get("auto_backup", True):
                self.backup_single_app(app_name)
            
            # Remove app file
            os.remove(app_path)
            
            # Update installed apps
            del self.installed_apps[app_name]
            
            return f"🗑️ **App uninstalled successfully!**\n\n**Name:** {app_name}\n**File removed:** {app_path}"
            
        except Exception as e:
            return f"❌ Uninstallation error: {e}"
    
    def update_app(self, app_name):
        """Update an app to the latest version"""
        if not app_name:
            return "❌ Please specify an app name to update"
        
        if app_name not in self.installed_apps:
            return f"❌ App '{app_name}' is not installed"
        
        # For now, simulate update checking
        # In a real implementation, this would check repositories for newer versions
        current_version = self.installed_apps[app_name]['metadata'].get('version', '1.0.0')
        
        return f"🔄 Update checking not yet implemented.\n\nCurrent version of '{app_name}': {current_version}\n\nWould check repositories for newer versions."
    
    def list_apps(self, list_type="installed"):
        """List apps based on type"""
        if list_type == "installed":
            if not self.installed_apps:
                return "📂 No apps currently installed"
            
            result = f"📂 **Installed Apps:** {len(self.installed_apps)}\n\n"
            
            for app_name, app_info in self.installed_apps.items():
                metadata = app_info['metadata']
                name = metadata.get('name', app_name)
                version = metadata.get('version', '1.0.0')
                description = metadata.get('description', 'No description')
                size = app_info['size']
                
                result += f"• **{name}** v{version}\n"
                result += f"  {description}\n"
                result += f"  File: {app_info['filename']} ({size} bytes)\n\n"
            
            return result
        
        elif list_type == "packages":
            if not self.packages:
                return "📦 No packages created"
            
            result = f"📦 **Created Packages:** {len(self.packages)}\n\n"
            
            for pkg_name, pkg_info in self.packages.items():
                manifest = pkg_info['manifest']
                result += f"• **{manifest['name']}** v{manifest['version']}\n"
                result += f"  {manifest['description']}\n"
                result += f"  Package: {os.path.basename(pkg_info['package_path'])}\n"
                result += f"  Created: {pkg_info['created'][:16]}\n\n"
            
            return result
        
        elif list_type == "repositories":
            return self.list_repositories()
        
        else:
            return f"❌ Unknown list type: {list_type}\nAvailable: installed, packages, repositories"
    
    def search_apps(self, query):
        """Search for apps"""
        if not query:
            return "❌ Please provide a search query"
        
        query = query.lower()
        results = []
        
        # Search installed apps
        for app_name, app_info in self.installed_apps.items():
            metadata = app_info['metadata']
            name = metadata.get('name', app_name).lower()
            description = metadata.get('description', '').lower()
            
            if query in name or query in description or query in app_name.lower():
                results.append({
                    'type': 'installed',
                    'name': metadata.get('name', app_name),
                    'version': metadata.get('version', '1.0.0'),
                    'description': metadata.get('description', 'No description'),
                    'app_name': app_name
                })
        
        # Search packages
        for pkg_name, pkg_info in self.packages.items():
            manifest = pkg_info['manifest']
            name = manifest.get('name', pkg_name).lower()
            description = manifest.get('description', '').lower()
            
            if query in name or query in description:
                results.append({
                    'type': 'package',
                    'name': manifest.get('name', pkg_name),
                    'version': manifest.get('version', '1.0.0'),
                    'description': manifest.get('description', 'No description'),
                    'package_name': pkg_name
                })
        
        if not results:
            return f"🔍 No apps found matching '{query}'"
        
        result = f"🔍 **Search Results for '{query}':** {len(results)} found\n\n"
        
        for item in results:
            result += f"• **{item['name']}** v{item['version']} ({item['type']})\n"
            result += f"  {item['description']}\n\n"
        
        return result
    
    def show_app_info(self, app_name):
        """Show detailed app information"""
        if not app_name:
            return "❌ Please specify an app name"
        
        if app_name in self.installed_apps:
            app_info = self.installed_apps[app_name]
            metadata = app_info['metadata']
            
            modified_time = datetime.fromtimestamp(app_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
            
            result = f"ℹ️ **App Information: {metadata.get('name', app_name)}**\n\n"
            result += f"**Version:** {metadata.get('version', '1.0.0')}\n"
            result += f"**Description:** {metadata.get('description', 'No description')}\n"
            result += f"**Author:** {metadata.get('author', 'Unknown')}\n"
            result += f"**File:** {app_info['filename']}\n"
            result += f"**Size:** {app_info['size']} bytes\n"
            result += f"**Modified:** {modified_time}\n"
            result += f"**Dependencies:** {', '.join(metadata.get('dependencies', [])) or 'None'}\n"
            result += f"**Status:** Installed\n"
            
            return result
        
        else:
            return f"❌ App '{app_name}' not found"
    
    def handle_repository_command(self, repo_cmd):
        """Handle repository management commands"""
        parts = repo_cmd.split(":", 1)
        action = parts[0]
        
        if action == "add":
            if len(parts) > 1:
                repo_parts = parts[1].split(":", 1)
                if len(repo_parts) == 2:
                    name, url = repo_parts
                    self.repositories[name] = url
                    self.save_repositories()
                    return f"✅ Added repository '{name}': {url}"
                else:
                    return "❌ Usage: deploy:repo:add:name:url"
            else:
                return "❌ Usage: deploy:repo:add:name:url"
        
        elif action == "remove":
            if len(parts) > 1:
                name = parts[1]
                if name in self.repositories:
                    del self.repositories[name]
                    self.save_repositories()
                    return f"🗑️ Removed repository '{name}'"
                else:
                    return f"❌ Repository '{name}' not found"
            else:
                return "❌ Usage: deploy:repo:remove:name"
        
        elif action == "list":
            return self.list_repositories()
        
        elif action == "update":
            # Refresh repository information
            return "🔄 Repository update not yet implemented"
        
        else:
            return "❌ Unknown repository command\nAvailable: add, remove, list, update"
    
    def list_repositories(self):
        """List configured repositories"""
        if not self.repositories:
            return "📁 No repositories configured"
        
        result = f"📁 **Configured Repositories:** {len(self.repositories)}\n\n"
        
        for name, url in self.repositories.items():
            status = "🌐" if url.startswith(('http://', 'https://')) else "📂"
            result += f"• {status} **{name}**\n"
            result += f"  {url}\n\n"
        
        return result
    
    def backup_apps(self):
        """Backup all installed apps"""
        if not self.installed_apps:
            return "📂 No apps to backup"
        
        try:
            backup_dir = self.config["backup_dir"]
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"apps_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, f"{backup_name}.zip")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup all app files
                for app_name, app_info in self.installed_apps.items():
                    zipf.write(app_info['path'], app_info['filename'])
                
                # Backup metadata
                metadata = {
                    'backup_date': datetime.now().isoformat(),
                    'apps': {name: info['metadata'] for name, info in self.installed_apps.items()},
                    'count': len(self.installed_apps)
                }
                
                metadata_json = json.dumps(metadata, indent=2)
                zipf.writestr("backup_metadata.json", metadata_json)
            
            return f"💾 **Backup created successfully!**\n\n**Backup:** {backup_path}\n**Apps included:** {len(self.installed_apps)}\n**Size:** {os.path.getsize(backup_path)} bytes"
            
        except Exception as e:
            return f"❌ Backup error: {e}"
    
    def backup_single_app(self, app_name):
        """Backup a single app"""
        if app_name not in self.installed_apps:
            return
        
        try:
            backup_dir = self.config["backup_dir"]
            os.makedirs(backup_dir, exist_ok=True)
            
            app_info = self.installed_apps[app_name]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{app_name}_backup_{timestamp}.py"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(app_info['path'], backup_path)
            
        except Exception as e:
            print(f"Warning: Failed to backup {app_name}: {e}")
    
    def restore_apps(self, backup_name):
        """Restore apps from backup"""
        if not backup_name:
            # List available backups
            backup_dir = self.config["backup_dir"]
            if not os.path.exists(backup_dir):
                return "📂 No backups found"
            
            backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
            if not backups:
                return "📂 No backup files found"
            
            result = f"📂 **Available Backups:** {len(backups)}\n\n"
            for backup in sorted(backups, reverse=True):
                result += f"• {backup}\n"
            
            result += "\n**To restore:** deploy:restore:backup_name"
            return result
        
        try:
            backup_dir = self.config["backup_dir"]
            backup_path = os.path.join(backup_dir, backup_name)
            
            if not backup_path.endswith('.zip'):
                backup_path += '.zip'
            
            if not os.path.exists(backup_path):
                return f"❌ Backup not found: {backup_name}"
            
            # Extract backup
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Read metadata
                metadata_path = os.path.join(temp_dir, "backup_metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    backup_date = metadata.get('backup_date', 'Unknown')
                    app_count = metadata.get('count', 0)
                else:
                    backup_date = 'Unknown'
                    app_count = 0
                
                # Restore app files
                restored = 0
                for filename in os.listdir(temp_dir):
                    if filename.endswith('.py') and filename != 'backup_metadata.json':
                        source = os.path.join(temp_dir, filename)
                        target = os.path.join("apps", filename)
                        
                        os.makedirs("apps", exist_ok=True)
                        shutil.copy2(source, target)
                        restored += 1
                
                # Rescan apps
                self.scan_installed_apps()
                
                return f"✅ **Restore completed!**\n\n**Backup date:** {backup_date[:19]}\n**Apps restored:** {restored}\n**Expected:** {app_count}"
                
        except Exception as e:
            return f"❌ Restore error: {e}"
    
    def validate_app(self, app_name):
        """Validate an app for deployment"""
        if not app_name:
            return "❌ Please specify an app name to validate"
        
        if app_name not in self.installed_apps:
            return f"❌ App '{app_name}' not found"
        
        app_info = self.installed_apps[app_name]
        app_path = app_info['path']
        
        validation_results = []
        errors = []
        warnings = []
        
        try:
            # Check syntax
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                import ast
                ast.parse(content)
                validation_results.append("✅ Python syntax is valid")
            except SyntaxError as e:
                errors.append(f"❌ Syntax error: {e}")
            
            # Check for required main() function
            if 'def main():' in content:
                validation_results.append("✅ main() function found")
            else:
                errors.append("❌ main() function not found")
            
            # Check for class definition
            if 'class ' in content:
                validation_results.append("✅ Class definition found")
            else:
                warnings.append("⚠️ No class definition found")
            
            # Check for execute_command method
            if 'def execute_command(' in content:
                validation_results.append("✅ execute_command() method found")
            else:
                warnings.append("⚠️ execute_command() method not found")
            
            # Check metadata
            metadata = app_info['metadata']
            if metadata['name'] != 'Unknown':
                validation_results.append("✅ App name defined")
            else:
                warnings.append("⚠️ App name not properly defined")
            
            if metadata['version'] != '1.0.0' or 'version' in content:
                validation_results.append("✅ Version defined")
            else:
                warnings.append("⚠️ Version not properly defined")
            
            # Check file size
            if app_info['size'] < 1024 * 1024:  # 1MB
                validation_results.append("✅ File size reasonable")
            else:
                warnings.append("⚠️ Large file size (>1MB)")
            
            # Check dependencies
            dangerous_imports = ['os.system', 'subprocess.call', 'eval', 'exec']
            for dangerous in dangerous_imports:
                if dangerous in content:
                    warnings.append(f"⚠️ Potentially dangerous import: {dangerous}")
            
            # Summary
            result = f"🔍 **Validation Results for '{app_name}':**\n\n"
            
            if validation_results:
                result += "**✅ Passed Checks:**\n"
                for check in validation_results:
                    result += f"  {check}\n"
                result += "\n"
            
            if warnings:
                result += "**⚠️ Warnings:**\n"
                for warning in warnings:
                    result += f"  {warning}\n"
                result += "\n"
            
            if errors:
                result += "**❌ Errors:**\n"
                for error in errors:
                    result += f"  {error}\n"
                result += "\n"
            
            if not errors:
                result += "**🎯 Overall Status:** Ready for deployment"
            else:
                result += "**🚫 Overall Status:** Not ready for deployment"
            
            return result
            
        except Exception as e:
            return f"❌ Validation error: {e}"
    
    def publish_app(self, app_name):
        """Publish an app to a repository"""
        if not app_name:
            return "❌ Please specify an app name to publish"
        
        # For now, simulate publishing
        return f"📤 Publishing not yet implemented.\n\nWould publish '{app_name}' to configured repositories."
    
    def calculate_checksum(self, file_path):
        """Calculate SHA256 checksum of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            return f"error_{e}"
    
    def handle_config(self, config_command):
        """Handle configuration commands"""
        if "=" in config_command:
            key, value_str = config_command.split("=", 1)
            key = key.strip()
            value_str = value_str.strip()
            
            # Type conversion
            try:
                if key in ["auto_backup", "verify_signatures", "allow_dev_apps"]:
                    value = value_str.lower() in ["true", "1", "yes"]
                else:
                    value = value_str
                
                self.config[key] = value
                self.save_config()
                return f"⚙️ Set {key} = {value}"
                
            except ValueError:
                return f"❌ Invalid value for {key}: {value_str}"
        else:
            key = config_command.strip()
            if key in self.config:
                return f"⚙️ {key} = {self.config[key]}"
            else:
                return f"❌ Config key '{key}' not found"
    
    def show_config(self):
        """Show all configuration settings"""
        result = "⚙️ **Deployment Configuration:**\n\n"
        for key, value in self.config.items():
            result += f"• {key} = {value}\n"
        
        result += "\n**To change:** deploy:config:key=value"
        return result
    
    def show_statistics(self):
        """Show deployment statistics"""
        installed_count = len(self.installed_apps)
        packages_count = len(self.packages)
        repos_count = len(self.repositories)
        
        # Calculate total size
        total_size = sum(app['size'] for app in self.installed_apps.values())
        
        # Backup info
        backup_dir = self.config["backup_dir"]
        backup_count = 0
        backup_size = 0
        
        if os.path.exists(backup_dir):
            backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
            backup_count = len(backups)
            backup_size = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in backups)
        
        result = f"""📊 **Deployment Statistics:**

**📱 Apps:**
• Installed apps: {installed_count}
• Created packages: {packages_count}
• Total app size: {total_size:,} bytes

**📁 Repositories:**
• Configured repositories: {repos_count}
• Default repository: {self.config.get('default_repo', 'None')}

**💾 Backups:**
• Backup count: {backup_count}
• Backup storage: {backup_size:,} bytes
• Auto-backup: {self.config.get('auto_backup', False)}

**⚙️ Settings:**
• Package format: {self.config.get('package_format', 'zip')}
• Verify signatures: {self.config.get('verify_signatures', False)}
• Allow dev apps: {self.config.get('allow_dev_apps', True)}
"""
        
        if self.installed_apps:
            result += f"\n**📋 Recent Apps:**"
            recent_apps = sorted(self.installed_apps.items(), 
                               key=lambda x: x[1]['modified'], reverse=True)[:5]
            
            for app_name, app_info in recent_apps:
                name = app_info['metadata'].get('name', app_name)
                version = app_info['metadata'].get('version', '1.0.0')
                modified = datetime.fromtimestamp(app_info['modified']).strftime('%Y-%m-%d')
                result += f"\n• {name} v{version} ({modified})"
        
        return result
    
    def show_help(self):
        """Show comprehensive help"""
        return """📦 **App Deployment & Package Manager Help:**

**📦 Packaging:**
• `deploy:package:app_name` - Create package from installed app
• `deploy:validate:app_name` - Validate app for deployment
• `deploy:publish:app_name` - Publish app to repository

**📥 Installation:**
• `deploy:install:package.pxapp` - Install from local package
• `deploy:install:https://example.com/app.pxapp` - Install from URL
• `deploy:install:repo:app_name` - Install from repository
• `deploy:install:app_name` - Install from default repository

**📋 Management:**
• `deploy:list` - List installed apps
• `deploy:list:packages` - List created packages
• `deploy:list:repositories` - List repositories
• `deploy:info:app_name` - Show detailed app information
• `deploy:search:query` - Search for apps

**🔄 Updates:**
• `deploy:update:app_name` - Update specific app
• `deploy:uninstall:app_name` - Uninstall app

**📁 Repositories:**
• `deploy:repo:list` - List repositories
• `deploy:repo:add:name:url` - Add repository
• `deploy:repo:remove:name` - Remove repository

**💾 Backup & Restore:**
• `deploy:backup` - Backup all apps
• `deploy:restore` - List available backups
• `deploy:restore:backup_name` - Restore from backup

**⚙️ Configuration:**
• `deploy:config` - Show all settings
• `deploy:config:auto_backup=true` - Enable auto-backup
• `deploy:config:package_format=zip` - Set package format

**📊 Information:**
• `deploy:stats` - Show deployment statistics

**💡 Examples:**
```
deploy:package:my_calculator
deploy:install:calculator.pxapp
deploy:install:official:web_scraper
deploy:backup
deploy:list:installed
deploy:search:calculator
deploy:validate:my_app
```

**📦 Package Format:**
PXBot apps are packaged as .pxapp files (ZIP format) containing:
• App Python file
• manifest.json with metadata
• README.md with documentation
• Optional dependencies and resources

**🔧 Development Workflow:**
1. Develop app in apps/ directory
2. Test app functionality
3. Validate with deploy:validate:app_name
4. Package with deploy:package:app_name
5. Share .pxapp file or publish to repository
"""
    
    def cleanup(self):
        """Cleanup when app is unloaded"""
        self.save_config()
        self.save_repositories()

# Required main function
def main():
    """Entry point for the deployment manager"""
    return AppDeploymentManager()

# For direct testing
if __name__ == "__main__":
    app = main()
    print("📦 App Deployment Manager Test")
    print("=" * 40)
    
    # Test basic functionality
    print(app.execute_command("deploy:list:installed"))
    print("\n" + app.execute_command("deploy:repo:list"))