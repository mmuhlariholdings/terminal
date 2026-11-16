# Terminal 1 keyboard cheat sheet

A user-facing summary for the BlackBerry Q20 keyboard on Terminal 1. The RP2040 firmware owns the
real key map, and **[firmware/keyboard-board/README.md](../firmware/keyboard-board/README.md) is the
authority**. If this page and the firmware README disagree, the firmware README is right; please fix this page.

Status: draft from the prototype plan. The `Fn` + letter assignments below are a **proposal** until
the firmware README lists them.

## The four keys above the keyboard

The Q20's navigation row has four keys and the trackpad. Left to right:

```
 [ Call ]  [ Menu ]   ( trackpad )   [ Back ]  [ End ]
   Ctrl      Esc       arrows/Enter     Tab       Fn
```

| Printed key | Terminal 1 key | Notes |
|---|---|---|
| Call (green) | `Ctrl` | sticky: tap it, then the letter (tap `Ctrl`, then `c` = Ctrl+C) |
| Menu | `Esc` | vim, less and Claude Code's "stop" key |
| Back | `Tab` | shell completion |
| End (red) | `Fn` | sticky, like `Ctrl` |

Holding `Fn` + `Back` while pressing the power button starts **service mode** (USB-C goes to the CM4
for flashing; see `system/plan/interfaces.md` section 6).

## Fn layer

### Function keys: `Fn` + the keys printed with digits

The Q20 has no number row; the digits are printed on letter keys and reached with `Alt`.
`Fn` + the key printed **1** gives **F1**, and so on up to **0**, which gives **F10**.

### Shell symbols: `Fn` + letters (proposal)

| Symbol | Keys | Memory aid |
|---|---|---|
| `\|` pipe | `Fn` + `P` | **P**ipe |
| `~` tilde | `Fn` + `T` | **T**ilde |
| `` ` `` backtick | `Fn` + `G` | **G**rave accent |
| `{` `}` | `Fn` + `U`, `Fn` + `I` | pair, next to each other |
| `[` `]` | `Fn` + `J`, `Fn` + `K` | pair, under `{` `}` |
| `<` `>` | `Fn` + `N`, `Fn` + `M` | pair, bottom row |
| `\` backslash | `Fn` + `B` | **B**ackslash |
| `^` caret | `Fn` + `C` | **C**aret |

## Alt: printed symbols

`Alt` + a key gives the symbol printed on it, as on a BlackBerry: digits, `@ # $ % & * ( ) - + = : ; ' " , . ? ! /`
and the rest of the printed punctuation.

## Trackpad

| Action | Arrow mode (default) | Mouse mode |
|---|---|---|
| Swipe | arrow keys (vim, tmux, shell history) | moves the pointer |
| Click | `Enter` | left click |
| Switch | `terminal-1-ctl trackpad mouse` | `terminal-1-ctl trackpad arrows` |

## Sticky keys

`Ctrl`, `Fn` and `Shift` can be tapped once instead of held: the next key gets the modifier.
Lock and cancel behaviour (double tap, tap again) is defined in the firmware README.

## Power button

| Press | What happens |
|---|---|
| Long press | clean shutdown (the keyboard sends the power key; Linux powers off, then the RP2040 cuts power) |
| Short press | screen off / on (proposal in `terminal-1-statusd`; the CM4 has no real sleep) |

## Everyday shortcuts on Terminal 1

| Keys | Does |
|---|---|
| `Ctrl` then `b`, then `v` / `s` | tmux: split side by side / top and bottom |
| `Ctrl` then `b`, then `c` / `n` / `p` | tmux: new window / next / previous |
| `Ctrl` then `b`, then trackpad swipe | tmux: move between panes |
| `Ctrl` then `b`, then `Shift`+`L` | lock the screen (asks for your password) |
| `Ctrl` then `b`, then `d` | detach; the session restarts and reattaches |
| `Ctrl` then `r` | search shell history |
| `Ctrl` then `c` / `d` | interrupt / end of input |
| `Esc` | stop Claude Code mid-answer |
| `Ctrl`+`Alt`+`F2` | text console login (fallback if the terminal ever fails) |

Shell helpers: `wifi` (network picker), `battery`, `lock`, `azlogin` (`az login --use-device-code`), `logout-cloud`.
