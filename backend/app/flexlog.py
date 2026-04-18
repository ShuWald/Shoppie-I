# Logging

from __future__ import annotations
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "Log"
MAIN_LOG_FILE = LOG_DIR / "main.log"
INFO_LOG_FILE = LOG_DIR / "info.log"


# Create Log directory and main log files
def ensure_log_directory() -> None:
	LOG_DIR.mkdir(parents=True, exist_ok=True)
	# Reset all existing log files at startup so each run starts clean.
	for existing_log in LOG_DIR.glob("*.log"):
		existing_log.write_text("", encoding="utf-8")
	# Ensure base log files exist even on first run.
	MAIN_LOG_FILE.touch(exist_ok=True)
	INFO_LOG_FILE.touch(exist_ok=True)


def _write_log(file_path: Path, entry: str) -> None:
	"""Write entry to log file. Assumes parent directory exists."""
	with file_path.open("a", encoding="utf-8") as log_file:
		log_file.write(entry)

# Cleans route names to create valid log file names
def _clean_route_name(route_name: str) -> str:
	cleaned_name = route_name.strip().replace("\\", "/").replace("/", "_")
	cleaned_name = cleaned_name.replace(" ", "_")
	return cleaned_name or "additional"


def _build_log_entry(message: str) -> str:
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	return f"[{timestamp}] {message}\n"


# Writes a log to main, optionally printing and/or logging to additional route
def log_message(message: str, print_log: bool = False, additional_route: str | None = None) -> None:
	entry = _build_log_entry(message)
	
	try:
		_write_log(MAIN_LOG_FILE, entry)
		
		if additional_route:
			route_file = LOG_DIR / f"{additional_route}.log"
			try:
				_write_log(route_file, entry)
			except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
				# If route file write fails, clean name and log cause
				cleaned_name = _clean_route_name(additional_route)
				route_file = LOG_DIR / f"{cleaned_name}.log"
				try:
					route_file.parent.mkdir(parents=True, exist_ok=True)
					_write_log(route_file, entry)
				except Exception as err:
					# Log the error with full traceback info to main log
					error_msg = f"ERROR writing to route '{additional_route}' (cleaned: '{cleaned_name}'): {type(err).__name__}: {err}"
					error_entry = _build_log_entry(error_msg)
					_write_log(MAIN_LOG_FILE, error_entry)
		
		if print_log:
			print(entry, end="")
	
	except Exception as e:
		# Critical error: main log write failed, just print to console
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print(f"[{timestamp}] CRITICAL LOGGING FAILURE: {type(e).__name__}: {e}")


ensure_log_directory()

