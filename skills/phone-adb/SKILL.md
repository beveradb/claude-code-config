---
name: phone-adb
description: Connect adb to Andrew's Android phone (Pixel 9 Pro) over Wi-Fi wireless debugging. Use whenever a session needs adb on his phone — installing/testing an APK, logcat, screenshots, screenrecord, `adb shell`, Expo/React Native on device — or he says "/phone-adb", "connect to my phone", "use my pixel", "adb to my phone". Run it BEFORE any other adb command.
---

# phone-adb — connect adb to Andrew's phone over Wi-Fi

The phone is paired with this Mac already; its wireless-debugging port changes on every
toggle/reboot, so never hardcode an address. The script finds it via adb's mDNS.

```bash
phone-adb                     # connect (or confirm); prints CONNECTED serial=IP:PORT model=...
phone-adb status              # adb devices + mDNS services (debugging)
phone-adb pair IP:PORT CODE   # only if the Mac was un-paired (see below)
phone-adb disconnect
```

(Script lives at `~/.claude/skills/phone-adb/scripts/phone-adb`, symlinked into `~/.local/bin`.)

## After connecting

- Use the printed serial for every command: `adb -s <serial> ...`, or prefix commands
  with `ANDROID_SERIAL=<serial>`. Emulators may also be attached, so don't rely on the default.
- Screenshots: `adb -s <serial> exec-out screencap -p > shot.png`, then Read the PNG.
- Andrew's Mac is resource-tight: don't start an emulator when the real phone is available.

## If it prints NOT CONNECTED

Relay its checklist to Andrew in one short message (wireless debugging on, same Wi-Fi,
no VPN) and wait. If he says the Mac isn't in the "Paired devices" list, ask him for the
IP:port and code from **Pair device with pairing code** and run `phone-adb pair IP:PORT CODE`.
A `protocol fault` from pairing usually means it's already paired; the script still
tries to connect afterwards, so check its final line.

## Staying connected (since 2026-10-26)

- After every successful connect, `phone-adb` runs `adb tcpip 5555` and switches to
  `<phone IP>:5555`. That fixed port survives adb server restarts and Wi-Fi blips, so later
  reconnects need no discovery. It lasts until the phone **reboots** or Wireless debugging is
  turned off; then one normal reconnect (toggle Wireless debugging on) pins it again.
- **Never run `adb kill-server` / restart the adb server** while the phone is in use: it
  drops the phone for every session (a Maestro agent did this on 2026-10-25). Recover a hung
  emulator with `adb -s emulator-NNNN reconnect` or by restarting the emulator instead.
- A pairing code works **once**. If `adb pair` fails, ask for a new code; don't retry.
- Right after pairing, mDNS often stops advertising the connect port: ask Andrew for the IP:port
  under "Device addresses & Port" and run `adb connect IP:PORT` once (then it pins :5555).
