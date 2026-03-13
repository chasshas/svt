"""SVT Core - App loader: discovers and loads apps from the apps directory."""

from __future__ import annotations
import os
import json
import importlib.util
from typing import Optional, TYPE_CHECKING

from svt.sdk.types import AppType, AppManifest, CommandDef
from svt.sdk.base import SVTApp

if TYPE_CHECKING:
    from svt.core.engine import SVTEngine


class ScriptApp(SVTApp):
    """Wrapper for script-type apps. Each command maps to a .svt script file."""

    def __init__(self, manifest: AppManifest):
        super().__init__(manifest)

    def execute_command(self, command_name: str, ctx):
        from svt.sdk.types import CommandResult
        cmd_def = self.manifest.commands.get(command_name)
        if not cmd_def:
            return CommandResult.error(f"Unknown command: {self.name}:{command_name}")
        if not cmd_def.file:
            return CommandResult.error(f"No script file for: {self.name}:{command_name}")

        script_path = os.path.join(self.manifest.path, cmd_def.file)
        if not os.path.isfile(script_path):
            return CommandResult.error(f"Script file not found: {script_path}")

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Parse header line for args/options definition
            script_lines = []
            if lines and lines[0].strip().startswith('#!svt'):
                header = lines[0].strip()[5:].strip()
                self._bind_script_params(header, ctx)
                script_lines = [l.rstrip('\n') for l in lines[1:]]
            else:
                script_lines = [l.rstrip('\n') for l in lines]

            result = ctx.execute_lines(script_lines)
            return result if result else CommandResult.success()
        except Exception as e:
            return CommandResult.error(f"Script error: {e}")

    def _bind_script_params(self, header: str, ctx):
        """Parse #!svt header and bind args/options to variables."""
        parts = header.split()
        positional_idx = 0
        i = 0
        while i < len(parts):
            part = parts[i]
            if part.startswith('--') or part.startswith('-'):
                # Option: --name/-n:type=default
                opt_spec = part
                opt_name = opt_spec.lstrip('-').split('/')[0].split(':')[0].split('=')[0]
                # Check short form
                short_names = []
                if '/' in opt_spec:
                    for segment in opt_spec.split('/'):
                        short_names.append(segment.lstrip('-').split(':')[0].split('=')[0])
                else:
                    short_names = [opt_name]
                # Find default
                default = None
                if '=' in opt_spec:
                    default = opt_spec.split('=', 1)[1]
                # Resolve from ctx.options
                value = default
                for sn in short_names:
                    if sn in ctx.options:
                        value = ctx.options[sn]
                        break
                if value is not None:
                    ctx.variables.set(opt_name, value)
            else:
                # Positional: name:type
                arg_name = part.split(':')[0]
                if positional_idx < len(ctx.args):
                    ctx.variables.set(arg_name, ctx.args[positional_idx])
                positional_idx += 1
            i += 1


class AppLoader:
    """Discovers and loads SVT apps from the filesystem."""

    def __init__(self, engine: SVTEngine):
        self.engine = engine
        self.apps_dirs: list[str] = []

    def add_apps_dir(self, path: str):
        if os.path.isdir(path):
            self.apps_dirs.append(os.path.abspath(path))

    def discover_all(self) -> dict[str, SVTApp]:
        """Scan all app directories and load apps."""
        apps = {}
        for apps_dir in self.apps_dirs:
            for entry in os.listdir(apps_dir):
                app_path = os.path.join(apps_dir, entry)
                if not os.path.isdir(app_path):
                    continue
                manifest_path = os.path.join(app_path, 'app.json')
                if not os.path.isfile(manifest_path):
                    continue
                app = self._load_app(app_path, manifest_path)
                if app:
                    apps[app.name] = app
        return apps

    def _load_app(self, app_path: str, manifest_path: str) -> Optional[SVTApp]:
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            manifest = AppManifest(
                name=data.get("name", os.path.basename(app_path)),
                version=data.get("version", "1.0.0"),
                app_type=AppType(data.get("type", "python")),
                description=data.get("description", ""),
                module=data.get("module", "app"),
                path=app_path,
            )

            # Parse command definitions
            for cmd_name, cmd_data in data.get("commands", {}).items():
                cmd_def = CommandDef(
                    name=cmd_name,
                    description=cmd_data.get("description", ""),
                    handler=cmd_data.get("handler"),
                    file=cmd_data.get("file"),
                    block=cmd_data.get("block", False),
                    args=cmd_data.get("args", []),
                    options=cmd_data.get("options", {}),
                )
                manifest.commands[cmd_name] = cmd_def

            # Load based on type
            if manifest.app_type == AppType.SCRIPT:
                return ScriptApp(manifest)
            elif manifest.app_type in (AppType.PYTHON, AppType.HYBRID):
                return self._load_python_app(manifest)

        except Exception as e:
            print(f"[SVT] Error loading app from {app_path}: {e}")
            return None

    def _load_python_app(self, manifest: AppManifest) -> Optional[SVTApp]:
        module_file = os.path.join(manifest.path, f"{manifest.module}.py")
        if not os.path.isfile(module_file):
            print(f"[SVT] Module not found: {module_file}")
            return None
        try:
            spec = importlib.util.spec_from_file_location(
                f"svt.apps.{manifest.name}.{manifest.module}", module_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for a class that inherits from SVTApp
            app_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, SVTApp)
                        and attr is not SVTApp):
                    app_class = attr
                    break

            if app_class:
                return app_class(manifest)
            else:
                print(f"[SVT] No SVTApp subclass found in {module_file}")
                return None
        except Exception as e:
            print(f"[SVT] Error loading module {module_file}: {e}")
            return None
