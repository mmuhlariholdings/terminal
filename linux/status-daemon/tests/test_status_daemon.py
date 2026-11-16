"""Host-side tests for terminal-1-statusd and terminal-1-ctl.

The keyboard board is faked with a pseudo-terminal (pty): the daemon opens the
pty's slave side through a symlink, exactly as it opens /dev/terminal-1-status
on the device, and the test plays the RP2040 on the master side.

Run from the repository root:
    python3 -m unittest discover -s linux/status-daemon/tests -v
Works on Linux and macOS. Needs no root and no hardware.
"""

import importlib.machinery
import importlib.util
import os
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON = os.path.join(HERE, "..", "terminal-1-statusd")
CONTROL = os.path.join(HERE, "..", "terminal-1-ctl")


def load_daemon_module():
    loader = importlib.machinery.SourceFileLoader("terminal_1_statusd", DAEMON)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


statusd = load_daemon_module()


class ParseLineTests(unittest.TestCase):
    def test_battery(self):
        self.assertEqual(statusd.parse_line("BAT 87 3950 discharging\r\n"),
                         {"type": "BAT", "percent": 87, "millivolts": 3950, "state": "discharging"})

    def test_battery_rejects_bad_values(self):
        for line in ("BAT 101 3950 full", "BAT x 3950 full", "BAT 50 3950 exploding", "BAT 50 3950"):
            self.assertEqual(statusd.parse_line(line)["type"], "INVALID", line)

    def test_power_events(self):
        for event in statusd.POWER_EVENTS:
            self.assertEqual(statusd.parse_line("PWR " + event), {"type": "PWR", "event": event})
        self.assertEqual(statusd.parse_line("PWR explode")["type"], "INVALID")

    def test_version_ok_err(self):
        self.assertEqual(statusd.parse_line("VER 0.1.0 bench-pico"),
                         {"type": "VER", "firmware": "0.1.0", "board": "bench-pico"})
        self.assertEqual(statusd.parse_line("VER 0.1.0")["board"], "unknown")
        self.assertEqual(statusd.parse_line("OK"), {"type": "OK"})
        self.assertEqual(statusd.parse_line("ERR bad argument"), {"type": "ERR", "text": "bad argument"})

    def test_blank_and_unknown(self):
        self.assertIsNone(statusd.parse_line("   "))
        self.assertEqual(statusd.parse_line("HELLO")["type"], "INVALID")


class CommandTests(unittest.TestCase):
    def test_valid_commands(self):
        self.assertEqual(statusd.validate_command("ver"), ("keyboard", "VER"))
        self.assertEqual(statusd.validate_command("BL 40"), ("keyboard", "BL 40"))
        self.assertEqual(statusd.validate_command("MODE Mouse"), ("keyboard", "MODE mouse"))
        self.assertEqual(statusd.validate_command("SCREEN off"), ("local", "SCREEN off"))
        self.assertEqual(statusd.validate_command("SCREEN 70"), ("local", "SCREEN 70"))

    def test_invalid_commands(self):
        for command in ("", "BL 101", "BL x", "MODE sideways", "REBOOT", "PING now"):
            with self.assertRaises(ValueError, msg=command):
                statusd.validate_command(command)


class FormatTests(unittest.TestCase):
    def test_tmux_line(self):
        base = {"connected": True, "battery_percent": 87, "battery_state": "discharging",
                "wifi_ssid": "home", "wifi_signal": 72}
        self.assertEqual(statusd.format_tmux(base), "BAT 87% | wifi 72% home")
        self.assertEqual(statusd.format_tmux(dict(base, battery_state="charging")), "CHG 87% | wifi 72% home")
        self.assertEqual(statusd.format_tmux(dict(base, battery_percent=9)), "BAT 9% LOW | wifi 72% home")
        self.assertEqual(statusd.format_tmux(dict(base, battery_state="no-battery")), "AC | wifi 72% home")
        self.assertEqual(statusd.format_tmux({"connected": False}), "kbd -- | wifi --")

    def test_status_lines(self):
        text = statusd.format_status({"connected": True, "battery_percent": None, "port": "/dev/x"})
        self.assertEqual(text, "battery_percent=\nconnected=1\nport=/dev/x\n")

    def test_nmcli(self):
        output = "no:40:neighbour\nyes:72:my\\:net\n"
        self.assertEqual(statusd.parse_nmcli_wifi(output), (72, "my:net"))
        self.assertEqual(statusd.parse_nmcli_wifi("no:40:x\n"), (None, None))


class FakeKeyboard:
    """The RP2040 side of the CDC port: a pty master behind a symlink."""

    def __init__(self, link_path):
        self.link_path = link_path
        self.master, self.slave = pty.openpty()
        self.buffer = b""
        if os.path.lexists(link_path):
            os.unlink(link_path)
        os.symlink(os.ttyname(self.slave), link_path)

    def send(self, line):
        os.write(self.master, (line + "\n").encode("ascii"))

    def expect_line(self, timeout=3.0):
        deadline = time.monotonic() + timeout
        while b"\n" not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError("keyboard got no line; buffer=%r" % self.buffer)
            ready, _, _ = select.select([self.master], [], [], remaining)
            if ready:
                self.buffer += os.read(self.master, 1024)
        line, self.buffer = self.buffer.split(b"\n", 1)
        return line.decode("ascii")

    def unplug(self):
        os.close(self.master)
        os.close(self.slave)
        os.unlink(self.link_path)


class DaemonIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="t1-")
        self.run_dir = os.path.join(self.directory, "run")
        self.port_link = os.path.join(self.directory, "terminal-1-status")
        self.poweroff_marker = os.path.join(self.directory, "poweroff-called")
        backlight = os.path.join(self.directory, "backlight", "panel")
        os.makedirs(backlight)
        self.brightness = os.path.join(backlight, "brightness")
        with open(os.path.join(backlight, "max_brightness"), "w") as handle:
            handle.write("200\n")
        with open(self.brightness, "w") as handle:
            handle.write("200\n")
        self.keyboard = FakeKeyboard(self.port_link)
        self.log = open(os.path.join(self.directory, "daemon.log"), "w")
        self.daemon = subprocess.Popen(
            [sys.executable, DAEMON, "--port", self.port_link, "--run-dir", self.run_dir,
             "--poweroff-command", "touch %s" % self.poweroff_marker,
             "--reply-timeout", "0.5", "--reconnect-seconds", "0.2",
             "--backlight-dir", os.path.dirname(backlight), "--input-glob", "",
             "--no-wifi", "--no-pyserial", "--verbose"],
            stdout=self.log, stderr=subprocess.STDOUT)
        self.wait_for_status("connected", "1")
        # On connect the daemon asks for the firmware version.
        self.assertEqual(self.keyboard.expect_line(), "VER")
        self.keyboard.send("VER 0.1.0 bench-pico")
        self.wait_for_status("firmware_version", "0.1.0")

    def tearDown(self):
        self.daemon.terminate()
        try:
            self.daemon.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.daemon.kill()
        self.log.close()
        if self.failed_output():
            with open(os.path.join(self.directory, "daemon.log")) as handle:
                sys.stderr.write("\n--- daemon log ---\n" + handle.read())
        for fd in (self.keyboard.master, self.keyboard.slave):
            try:
                os.close(fd)
            except OSError:
                pass
        shutil.rmtree(self.directory, ignore_errors=True)

    def failed_output(self):
        outcome = getattr(self, "_outcome", None)
        result = getattr(outcome, "result", None)
        return bool(result and (result.failures or result.errors))

    def read_status(self):
        try:
            with open(os.path.join(self.run_dir, "status")) as handle:
                return dict(line.split("=", 1) for line in handle.read().splitlines() if "=" in line)
        except FileNotFoundError:
            return {}

    def wait_for_status(self, key, value, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.read_status().get(key) == value:
                return
            time.sleep(0.05)
        self.fail("status %s never became %r; last: %r" % (key, value, self.read_status()))

    def control(self, *arguments):
        return subprocess.run(
            [sys.executable, CONTROL, "--socket", os.path.join(self.run_dir, "control.sock")] + list(arguments),
            capture_output=True, text=True, timeout=10)

    def control_async(self, *arguments):
        return subprocess.Popen(
            [sys.executable, CONTROL, "--socket", os.path.join(self.run_dir, "control.sock")] + list(arguments),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_battery_updates_status_files(self):
        self.keyboard.send("BAT 87 3950 discharging")
        self.wait_for_status("battery_percent", "87")
        status = self.read_status()
        self.assertEqual(status["battery_millivolts"], "3950")
        self.assertEqual(status["battery_state"], "discharging")
        self.assertEqual(status["board_revision"], "bench-pico")
        with open(os.path.join(self.run_dir, "status.tmux")) as handle:
            self.assertEqual(handle.read().strip(), "BAT 87% | wifi --")
        # Garbage and half lines must not crash the daemon.
        os.write(self.keyboard.master, b"\x00\xffnonsense\nBAT 12 3500 charging\n")
        self.wait_for_status("battery_state", "charging")

    def test_trackpad_mode_round_trip(self):
        process = self.control_async("trackpad", "mouse")
        self.assertEqual(self.keyboard.expect_line(), "MODE mouse")
        self.keyboard.send("OK")
        output, _ = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output.strip(), "OK")

    def test_keyboard_backlight_error_is_reported(self):
        process = self.control_async("keyboard-backlight", "40")
        self.assertEqual(self.keyboard.expect_line(), "BL 40")
        self.keyboard.send("ERR no backlight fitted")
        output, _ = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(output.strip(), "ERR no backlight fitted")

    def test_unsolicited_lines_do_not_answer_a_pending_command(self):
        process = self.control_async("version")
        self.assertEqual(self.keyboard.expect_line(), "VER")
        self.keyboard.send("BAT 50 3800 discharging")
        self.keyboard.send("VER 0.2.0 rev-a")
        output, _ = process.communicate(timeout=5)
        self.assertEqual(output.strip(), "VER 0.2.0 rev-a")
        self.wait_for_status("board_revision", "rev-a")
        self.assertEqual(self.read_status()["battery_percent"], "50")

    def test_ping_timeout(self):
        process = self.control_async("ping")
        self.assertEqual(self.keyboard.expect_line(), "PING")
        output, _ = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(output.strip(), "ERR timeout")
        # The daemon is still usable afterwards.
        process = self.control_async("ping")
        self.assertEqual(self.keyboard.expect_line(), "PING")
        self.keyboard.send("OK")
        output, _ = process.communicate(timeout=5)
        self.assertEqual(output.strip(), "OK")

    def test_bad_usage(self):
        result = self.control("trackpad", "sideways")
        self.assertEqual(result.returncode, 2)
        result = self.control("keyboard-backlight", "101")
        self.assertEqual(result.returncode, 2)

    def test_status_command(self):
        result = self.control("status")
        self.assertEqual(result.returncode, 0)
        self.assertIn("connected=1", result.stdout)
        self.assertIn("firmware_version=0.1.0", result.stdout)

    def test_screen_brightness_and_power_button(self):
        result = self.control("screen", "50")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(self.brightness) as handle:
            self.assertEqual(handle.read().strip(), "100")
        self.keyboard.send("PWR button-short")
        self.wait_for_status("screen", "manual-off")
        with open(self.brightness) as handle:
            self.assertEqual(handle.read().strip(), "0")
        self.keyboard.send("PWR button-short")
        self.wait_for_status("screen", "on")
        with open(self.brightness) as handle:
            self.assertEqual(handle.read().strip(), "100")

    def test_critical_battery_powers_off_once(self):
        self.keyboard.send("PWR low-battery")
        self.wait_for_status("last_power_event", "low-battery")
        self.assertFalse(os.path.exists(self.poweroff_marker))
        self.keyboard.send("PWR critical-battery")
        deadline = time.monotonic() + 5
        while not os.path.exists(self.poweroff_marker) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(os.path.exists(self.poweroff_marker), "poweroff command was not run")
        os.unlink(self.poweroff_marker)
        self.keyboard.send("PWR critical-battery")
        time.sleep(0.5)
        self.assertFalse(os.path.exists(self.poweroff_marker), "poweroff ran twice")

    def test_reconnects_when_port_disappears(self):
        self.keyboard.unplug()
        self.wait_for_status("connected", "0")
        result = self.control("ping")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), "ERR keyboard not connected")
        self.keyboard = FakeKeyboard(self.port_link)
        self.wait_for_status("connected", "1")
        self.assertEqual(self.keyboard.expect_line(), "VER")
        self.keyboard.send("VER 0.1.1 bench-pico")
        self.wait_for_status("firmware_version", "0.1.1")


class IdleDimmingTests(unittest.TestCase):
    """Drives StatusDaemon.check_idle directly with a fake clock and fake sysfs."""

    def test_dim_off_and_wake(self):
        directory = tempfile.mkdtemp(prefix="t1-idle-")
        try:
            panel = os.path.join(directory, "panel")
            os.makedirs(panel)
            for name, value in (("max_brightness", "100"), ("brightness", "80")):
                with open(os.path.join(panel, name), "w") as handle:
                    handle.write(value)
            options = statusd.build_parser().parse_args(
                ["--backlight-dir", directory, "--run-dir", os.path.join(directory, "run"),
                 "--idle-dim-seconds", "60", "--idle-off-seconds", "180", "--dim-percent", "10"])
            daemon = statusd.StatusDaemon(options)
            daemon.screen_level = daemon.backlight.get_percent()
            brightness = os.path.join(panel, "brightness")

            def level():
                with open(brightness) as handle:
                    return int(handle.read())

            daemon.last_activity = time.monotonic() - 61
            daemon.check_idle()
            self.assertEqual((daemon.screen_mode, level()), ("dim", 10))
            daemon.last_activity = time.monotonic() - 181
            daemon.check_idle()
            self.assertEqual((daemon.screen_mode, level()), ("off", 0))
            daemon.activity()
            self.assertEqual((daemon.screen_mode, level()), ("on", 80))
        finally:
            shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
