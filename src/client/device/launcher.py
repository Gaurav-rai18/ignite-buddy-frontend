"""The only module that touches the OS to open/run things. Tests inject a fake."""
import os
import shutil
import subprocess
import sys
import base64
import webbrowser
from pathlib import Path


class SystemLauncher:
    supports_native = sys.platform == "win32"        # Task Scheduler / toast / Recycle Bin / lock / clipboard

    def open_path(self, p: str):
        if sys.platform == "win32":
            os.startfile(p)                                    # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])

    def launch_app(self, path: str):
        if sys.platform == "win32":
            os.startfile(path)                                 # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", path])
        else:
            subprocess.Popen(["gtk-launch", os.path.splitext(os.path.basename(path))[0]])

    def which(self, exe: str):
        return shutil.which(exe)

    def spawn(self, argv: list[str]):
        subprocess.Popen(argv)                                 # list args, shell=False

    def run(self, argv: list[str], cwd: str, timeout: int):
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=False)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def open_url(self, url: str):
        webbrowser.open(url)

    # ---- Windows integration ----
    def open_uri(self, uri: str):
        if sys.platform == "win32":
            os.startfile(uri)                                  # noqa  (names come from systemtargets.TARGETS only)
        else:
            raise OSError("This works on Windows only")

    def start_exe(self, exe: str):
        subprocess.Popen([exe])

    def powershell(self, script: str):
        enc = base64.b64encode(script.encode("utf-16-le")).decode()
        r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                           capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def lock(self):
        """Lock the current Windows workstation session."""
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])

    def clipboard_set(self, text: str):
        """Copy the provided text to the system clipboard.

        On Windows (including Accops VDI virtual desktop sessions), uses clip.exe.
        Encoding with 'utf-16' generates the required Byte Order Mark (BOM: \xff\xfe),
        ensuring Windows interprets the standard input stream as multi-byte Unicode
        rather than legacy single-byte OEM/ANSI text.
        """
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode("utf-16"), check=True, timeout=10)
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True, timeout=10)
        else:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True, timeout=10)

    def trash(self, path: str):
        """Recycle Bin on Windows; elsewhere a recoverable ~/.assistant_trash."""
        if sys.platform == "win32":
            p = path.replace("'", "''")
            kind = "DeleteDirectory" if os.path.isdir(path) else "DeleteFile"
            code, out = self.powershell("Add-Type -AssemblyName Microsoft.VisualBasic\n"
                                        f"[Microsoft.VisualBasic.FileIO.FileSystem]::{kind}('{p}', 'OnlyErrorDialogs', 'SendToRecycleBin')")
            if code:
                raise OSError(out.strip()[:200] or "could not move to the Recycle Bin")
        else:
            dest = Path.home() / ".assistant_trash"
            dest.mkdir(exist_ok=True)
            shutil.move(path, str(dest / Path(path).name))
