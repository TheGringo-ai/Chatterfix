#!/usr/bin/env python3
"""
Memory Guardian - Prevents VS Code crashes from memory pressure
Runs in background, monitors memory, and proactively frees resources
Does NOT interfere with builds or deployments
"""

import subprocess
import time
import os
import sys
import signal
import logging
from datetime import datetime
from pathlib import Path

# Configuration
MEMORY_WARNING_THRESHOLD = 85  # Warn at 85% memory usage
MEMORY_CRITICAL_THRESHOLD = 90  # Take action at 90%
CHECK_INTERVAL = 30  # Check every 30 seconds
LOG_FILE = Path.home() / ".memory-guardian.log"

# Protected processes (won't be killed during cleanup)
PROTECTED_PROCESSES = [
    "deploy", "build", "npm", "pip", "pytest", "docker", "git",
    "python", "node", "gcloud", "firebase", "make", "gcc", "clang"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryGuardian:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        logger.info("Memory Guardian shutting down...")
        self.running = False

    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics"""
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True
            )

            lines = result.stdout.strip().split('\n')
            stats = {}
            page_size = 16384  # macOS default

            for line in lines:
                if ':' in line:
                    key, value = line.split(':')
                    value = value.strip().replace('.', '')
                    if value.isdigit():
                        stats[key.strip()] = int(value) * page_size

            # Get total memory
            total_result = subprocess.run(
                ["sysctl", "hw.memsize"],
                capture_output=True,
                text=True
            )
            total_mem = int(total_result.stdout.split(':')[1].strip())

            # Calculate usage
            free = stats.get('Pages free', 0)
            inactive = stats.get('Pages inactive', 0)
            speculative = stats.get('Pages speculative', 0)
            available = free + inactive + speculative

            used = total_mem - available
            percent_used = (used / total_mem) * 100

            return {
                "total": total_mem,
                "used": used,
                "available": available,
                "percent_used": percent_used
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"percent_used": 0}

    def is_process_protected(self, process_name: str) -> bool:
        """Check if process should be protected from cleanup"""
        process_lower = process_name.lower()
        for protected in PROTECTED_PROCESSES:
            if protected in process_lower:
                return True
        return False

    def get_heavy_processes(self) -> list:
        """Get list of heavy memory consuming processes"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )

            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            processes = []

            for line in lines:
                parts = line.split()
                if len(parts) >= 11:
                    pid = parts[1]
                    mem_percent = float(parts[3])
                    command = ' '.join(parts[10:])

                    if mem_percent > 2.0:  # Only include if using >2% memory
                        processes.append({
                            "pid": pid,
                            "mem_percent": mem_percent,
                            "command": command
                        })

            return sorted(processes, key=lambda x: x['mem_percent'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting process list: {e}")
            return []

    def clear_system_caches(self):
        """Clear system caches safely"""
        try:
            # Clear inactive memory (safe operation)
            subprocess.run(
                ["sudo", "-n", "purge"],
                capture_output=True,
                timeout=10
            )
            logger.info("Cleared system caches")
        except subprocess.TimeoutExpired:
            logger.warning("Cache clear timed out")
        except Exception as e:
            # purge requires sudo, may fail without password
            logger.debug(f"Could not clear caches: {e}")

    def notify_user(self, title: str, message: str):
        """Send macOS notification"""
        try:
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}"'
            ], capture_output=True, timeout=5)
        except Exception:
            pass

    def suggest_cleanup(self, heavy_processes: list):
        """Suggest which processes to close"""
        suggestions = []
        for proc in heavy_processes[:5]:
            if not self.is_process_protected(proc['command']):
                suggestions.append(f"  - {proc['command'][:50]}... ({proc['mem_percent']:.1f}%)")

        if suggestions:
            logger.warning("Consider closing these high-memory processes:")
            for s in suggestions:
                logger.warning(s)

    def restart_vscode_extension_host(self):
        """Restart VS Code extension host to free memory (non-destructive)"""
        try:
            # Find VS Code extension host processes using significant memory
            result = subprocess.run(
                ["pgrep", "-f", "extensionHost"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        # Get memory usage of this process
                        ps_result = subprocess.run(
                            ["ps", "-p", pid, "-o", "pmem="],
                            capture_output=True,
                            text=True
                        )
                        if ps_result.returncode == 0:
                            mem = float(ps_result.stdout.strip() or "0")
                            if mem > 5.0:  # Only if using >5% memory
                                logger.info(f"VS Code extension host using {mem:.1f}% memory")
                                # Don't kill, just log - let user decide
        except Exception as e:
            logger.debug(f"Could not check extension host: {e}")

    def run(self):
        """Main monitoring loop"""
        logger.info("Memory Guardian started")
        logger.info(f"Warning threshold: {MEMORY_WARNING_THRESHOLD}%")
        logger.info(f"Critical threshold: {MEMORY_CRITICAL_THRESHOLD}%")
        logger.info(f"Check interval: {CHECK_INTERVAL}s")

        last_warning_time = 0
        warning_cooldown = 300  # Don't warn more than once per 5 minutes

        while self.running:
            try:
                mem = self.get_memory_usage()
                percent = mem.get('percent_used', 0)

                current_time = time.time()

                if percent >= MEMORY_CRITICAL_THRESHOLD:
                    logger.critical(f"CRITICAL: Memory at {percent:.1f}%")

                    # Notify user
                    if current_time - last_warning_time > warning_cooldown:
                        self.notify_user(
                            "Memory Critical",
                            f"Memory at {percent:.1f}%. Consider closing some apps."
                        )
                        last_warning_time = current_time

                    # Try to clear caches
                    self.clear_system_caches()

                    # Show suggestions
                    heavy = self.get_heavy_processes()
                    self.suggest_cleanup(heavy)

                    # Check VS Code extension host
                    self.restart_vscode_extension_host()

                elif percent >= MEMORY_WARNING_THRESHOLD:
                    logger.warning(f"WARNING: Memory at {percent:.1f}%")

                    if current_time - last_warning_time > warning_cooldown:
                        self.notify_user(
                            "Memory Warning",
                            f"Memory at {percent:.1f}%. Monitor usage."
                        )
                        last_warning_time = current_time
                else:
                    logger.debug(f"Memory OK: {percent:.1f}%")

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(CHECK_INTERVAL)

        logger.info("Memory Guardian stopped")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            guardian = MemoryGuardian()
            mem = guardian.get_memory_usage()
            print(f"Memory Usage: {mem['percent_used']:.1f}%")
            print(f"Available: {mem['available'] / (1024**3):.1f} GB")
            print(f"Used: {mem['used'] / (1024**3):.1f} GB")
            print(f"Total: {mem['total'] / (1024**3):.1f} GB")

            if mem['percent_used'] >= MEMORY_CRITICAL_THRESHOLD:
                print("\nSTATUS: CRITICAL")
            elif mem['percent_used'] >= MEMORY_WARNING_THRESHOLD:
                print("\nSTATUS: WARNING")
            else:
                print("\nSTATUS: OK")

            print("\nTop memory consumers:")
            for proc in guardian.get_heavy_processes()[:5]:
                print(f"  {proc['mem_percent']:.1f}% - {proc['command'][:60]}")

        elif cmd == "clear":
            guardian = MemoryGuardian()
            guardian.clear_system_caches()
            print("Attempted to clear system caches")

        elif cmd == "help":
            print("Memory Guardian - VS Code Crash Prevention")
            print("\nUsage:")
            print("  python memory-guardian.py          Start monitoring daemon")
            print("  python memory-guardian.py status   Check current memory status")
            print("  python memory-guardian.py clear    Clear system caches")
            print("  python memory-guardian.py help     Show this help")
            print(f"\nLog file: {LOG_FILE}")

        else:
            print(f"Unknown command: {cmd}")
            print("Use 'help' for usage information")
    else:
        guardian = MemoryGuardian()
        guardian.run()


if __name__ == "__main__":
    main()
