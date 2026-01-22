# Setup.py
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

VENV_DIR = ROOT / ".venv"
INSTANCE_DIR = ROOT / "instance"

HASH_FILE = ROOT / "hash_save.txt"
ENV_PS1 = ROOT / "set_env.ps1"
RUN_PS1 = ROOT / "run.ps1"
RUN_CMD = ROOT / "run.cmd"

FIXED_GITHUB_REPO = "TroLyAmazon/VietUptime"


def ask_yn(prompt: str, default_yes: bool = True) -> bool:
    default = "Y/n" if default_yes else "y/N"
    while True:
        s = input(f"{prompt} ({default}): ").strip().lower()
        if not s:
            return default_yes
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Chỉ nhập Y hoặc N.")


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def venv_python_path() -> Path:
    # Windows
    py_win = VENV_DIR / "Scripts" / "python.exe"
    if py_win.exists():
        return py_win
    # Linux/macOS
    py_nix = VENV_DIR / "bin" / "python"
    return py_nix


def safe_delete(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except Exception:
            pass


def main():
    print("=== DotStatus / VietUptime Setup ===")
    print(f"Project: {ROOT}")
    print(f'GITHUB_REPO (fixed): "{FIXED_GITHUB_REPO}"')

    # 1) Xóa setup cũ?
    if ask_yn("Xóa Setup cũ không? (hash_save.txt, set_env.ps1, run.ps1, run.cmd)", default_yes=True):
        safe_delete(HASH_FILE)
        safe_delete(ENV_PS1)
        safe_delete(RUN_PS1)
        safe_delete(RUN_CMD)

    # 2) Xóa .venv + instance?
    if ask_yn("Xóa file cũ .venv và instance không?", default_yes=True):
        safe_delete(VENV_DIR)
        safe_delete(INSTANCE_DIR)

    # 3) Tạo mới?
    if not ask_yn("Tạo mới chứ? (tạo venv + cài requirements + tạo hash)", default_yes=True):
        print("Bạn chọn không tạo mới. Dừng setup.")
        return

    # ---- Config (theo default bạn muốn) ----
    print("\n--- Config ---")
    secret_key = input('SECRET_KEY (default: "dev-please-change-me"): ').strip() or "dev-please-change-me"
    owner_username = input('OWNER_USERNAME (default: "admin"): ').strip() or "admin"
    owner_password = input('OWNER_PASSWORD (default: "admin123"): ').strip() or "admin123"
    timezone = input('TIMEZONE (default: "Asia/Bangkok"): ').strip() or "Asia/Bangkok"
    github_repo = FIXED_GITHUB_REPO

    # ---- Create venv ----
    print("\n--- Create venv ---")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])

    vpy = venv_python_path()
    if not vpy.exists():
        raise RuntimeError(f"Không tìm thấy python trong venv: {vpy}")

    # ---- Install requirements ----
    print("\n--- Install requirements ---")
    run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"])

    req = ROOT / "requirements.txt"
    if not req.exists():
        raise RuntimeError("Không thấy requirements.txt ở root project.")
    run([str(vpy), "-m", "pip", "install", "-r", str(req)])

    # ---- Generate OWNER_PASSWORD_HASH ----
    print("\n--- Generate OWNER_PASSWORD_HASH ---")
    gen_code = (
        "from werkzeug.security import generate_password_hash; "
        f"print(generate_password_hash({owner_password!r}))"
    )
    owner_password_hash = subprocess.check_output([str(vpy), "-c", gen_code], text=True).strip()
    print("OWNER_PASSWORD_HASH =", owner_password_hash)

    # ---- Test hash -> True? ----
    print("\n--- Test password hash ---")
    test_code = (
        "from werkzeug.security import check_password_hash; "
        f"print(check_password_hash({owner_password_hash!r}, {owner_password!r}))"
    )
    test_out = subprocess.check_output([str(vpy), "-c", test_code], text=True).strip()
    print("check_password_hash =>", test_out)
    ok = (test_out.lower() == "true")

    # ---- Save hash_save.txt (theo yêu cầu bạn) ----
    print("\n--- Save hash_save.txt ---")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HASH_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}]\n")
        f.write(f"SECRET_KEY={secret_key}\n")
        f.write(f"OWNER_USERNAME={owner_username}\n")
        f.write(f"OWNER_PASSWORD={owner_password}\n")
        f.write(f"OWNER_PASSWORD_HASH={owner_password_hash}\n")
        f.write(f"TIMEZONE={timezone}\n")
        f.write(f"GITHUB_REPO={github_repo}\n")
        f.write("\n")
    print(f"Saved: {HASH_FILE}")
    print("⚠️ hash_save.txt chứa mật khẩu plain theo yêu cầu bạn — đừng public / push lên GitHub.")

    # ---- Generate set_env.ps1 (tham khảo) ----
    print("\n--- Generate set_env.ps1 ---")
    ps1_lines = [
        f'$env:SECRET_KEY="{secret_key}"',
        f'$env:OWNER_USERNAME="{owner_username}"',
        f"$env:OWNER_PASSWORD_HASH='{owner_password_hash}'",  # dùng quote đơn vì có ký tự $
        f'$env:TIMEZONE="{timezone}"',
        f'$env:GITHUB_REPO="{github_repo}"',
        "",
    ]
    ENV_PS1.write_text("\n".join(ps1_lines), encoding="utf-8")
    print(f"Created: {ENV_PS1}")

    # ---- Generate run.ps1 (KHÔNG cần Activate/dot-source) ----
    print("\n--- Generate run.ps1 ---")
    run_ps1_lines = [
        "# Auto-generated by Setup.py",
        '$ErrorActionPreference = "Stop"',
        f'$env:SECRET_KEY="{secret_key}"',
        f'$env:OWNER_USERNAME="{owner_username}"',
        f"$env:OWNER_PASSWORD_HASH='{owner_password_hash}'",
        f'$env:TIMEZONE="{timezone}"',
        f'$env:GITHUB_REPO="{github_repo}"',
        "",
        # run with venv python directly
        '& "$PSScriptRoot\\.venv\\Scripts\\python.exe" "$PSScriptRoot\\run.py"',
        "",
    ]
    RUN_PS1.write_text("\n".join(run_ps1_lines), encoding="utf-8")
    print(f"Created: {RUN_PS1}")

    # ---- Generate run.cmd (double click) ----
    print("\n--- Generate run.cmd ---")
    run_cmd_lines = [
        "@echo off",
        "setlocal",
        f'set SECRET_KEY={secret_key}',
        f'set OWNER_USERNAME={owner_username}',
        f'set OWNER_PASSWORD_HASH={owner_password_hash}',
        f'set TIMEZONE={timezone}',
        f'set GITHUB_REPO={github_repo}',
        "",
        r'".\.venv\Scripts\python.exe" ".\run.py"',
        "endlocal",
        "",
        "pause",
    ]
    RUN_CMD.write_text("\n".join(run_cmd_lines), encoding="utf-8")
    print(f"Created: {RUN_CMD}")

    # ---- Result ----
    print("\n=== RESULT ===")
    if ok:
        print("✅ Setup thành công (hash test TRUE).")
    else:
        print("❌ Setup FAIL (hash test không TRUE).")

    print("\n=== RUN (no venv activate needed) ===")
    print(r"PowerShell:  .\run.ps1")
    print(r"CMD:         run.cmd")

    print("\nNếu PowerShell bị chặn script, chạy 1 lần trong cửa sổ đó:")
    print(r"  Set-ExecutionPolicy -Scope Process Bypass -Force")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("\n❌ Lệnh bị lỗi:", e)
        sys.exit(1)
    except Exception as e:
        print("\n❌ Setup error:", e)
        sys.exit(1)
