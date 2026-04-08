#! /usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Terminal RPN Calculator - A high-precision, feature-rich Reverse Polish Notation calculator for the terminal.
# Copyright (C) 2026 Simon Widmer - sery(at)solnet.ch

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# -------------------------
# General imports
# -------------------------
import math
import random
import sys
import time
import os
import signal
import ctypes

# -------------------------
# Platform specific imports
# -------------------------
if os.name == "nt":
    import msvcrt

    # enable ANSI escape codes on Windows
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)

    mode = ctypes.c_uint()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))

    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

    # ignore CTRL-C on Windows
    signal.signal(signal.SIGINT, signal.SIG_IGN)

else:
    import tty
    import termios

APPNAME = "Terminal RPN Calculator"
VERSION = "v1.7"
AUTHOR = "Simon Widmer"
EMAIL = "sery(at)solnet.ch"




# VT100 Escape Sequences
CLS, HOME, RESET, BOLD, UNDERLINE, ITALIC = "\x1b[2J", "\x1b[H", "\x1b[0m", "\x1b[1m", "\x1b[4m", "\x1b[3m"
CURSORHIDE, CURSORSHOW = "\x1b[?25l", "\x1b[?25h"
CURSORLEFT = "\033[D"
CURSORRIGHT = "\033[C"
CLEAR_SCROLLBACK = "\x1b[3J"
ERASELINE = "\x1b[2K"
ERASEDOWN = "\x1b[0J"
WHITE, RED = "\x1b[97m", "\x1b[91m"
LIGHTGRAY, DARKGRAY = "\x1b[37m", "\x1b[90m"
ORANGEONBROWN = "\x1b[38;5;214m\x1b[48;5;94m"
# inverse black font on white background for footer of help UI
FOOTER = "\x1b[7m"

# Internal scale: 10^16 for zero-noise math
SCALE_POW = 16
SCALE = 10**SCALE_POW
DISPLAY_DIGITS = SCALE_POW
THOUSAND_SEP = "'"
MAX_DIGITS = 31 # including THOUSAND_SEP's and possible '-' sign, to prevent overflow and UI issues
MAX_DISPLAY_WIDTH = 42  # max chars available per stack row (matches UI box)
stack = [] # Unlimited dynamic stack
display_mode = "dec"
display_format = "fix"   # "fix", "sci", "eng"
setwordsize = 64 # for logic operations, the default word size is 64 bits

error_displayed = False
def show_error(msg):
    global error_displayed
    if not error_displayed:
        sys.stdout.write(f"\r\n{BOLD}{RED}{msg}{RESET}")
        sys.stdout.flush()
        time.sleep(2)
        error_displayed = True

# -------------------------
# High-precision constants
# -------------------------
PI_INT = int(math.pi * SCALE)
TAU_INT = int(2 * math.pi * SCALE)
C_INT = int(299792458 * SCALE) # speed of light in m/s
E_INT  = int(math.e * SCALE)
G_INT = int(9.80665 * SCALE) # gravitational constant in m/s^2
PHI_INT = int(((1 + math.sqrt(5)) / 2) * SCALE) # golden ratio


# Converts user input string to a scaled integer for internal calculations.
def to_fixed(s):
    try:
        s = s.strip().lower()

        # --- HEX INPUT ---
        if s.startswith("0x"):
            return int(s, 16) * SCALE

        if display_mode == "hex":
            try:
                return int(s, 16) * SCALE
            except ValueError:
                return None

        # --- BINARY INPUT ---
        if s.startswith("0b"):
            return int(s, 2) * SCALE

        if display_mode == "bin":
            try:
                return int(s, 2) * SCALE
            except ValueError:
                return None

        # --- OCTAL INPUT ---
        if s.startswith("0o"):
            return int(s, 8) * SCALE

        if display_mode == "oct":
            try:
                return int(s, 8) * SCALE
            except ValueError:
                return None

        # --- DECIMAL INPUT ---
        if "." not in s:
            return int(s) * SCALE

        parts = s.split(".")
        w_part = parts[0] if parts[0] not in ("", "-") else ("0" if "-" not in parts[0] else "-0")
        f_part = (parts[1] + "0" * SCALE_POW)[:SCALE_POW]

        val = abs(int(w_part)) * SCALE + int(f_part)
        return -val if s.startswith("-") else val

    except Exception:
        return None

# Formats the scaled integer back to a string for display, respecting
# the current display mode (dec, hex, bin, oct) and display_format (fix, sci, eng).
def format_val(val_int):
    try:
        is_neg = val_int < 0
        v = abs(val_int)

        # --- HEX ---
        if display_mode == "hex":
            if is_neg:
                mask = (1 << setwordsize) - 1
                twos = (-( v // SCALE)) & mask
                result = f"0x{twos:X}"
            else:
                result = f"0x{v // SCALE:X}"
        # --- OCT ---
        elif display_mode == "oct":
            if is_neg:
                mask = (1 << setwordsize) - 1
                twos = (-(v // SCALE)) & mask
                result = f"0o{twos:o}"
            else:
                result = f"0o{v // SCALE:o}"
        # --- BIN ---
        elif display_mode == "bin":
            if is_neg:
                mask = (1 << setwordsize) - 1
                twos = (-(v // SCALE)) & mask
                result = f"0b{twos:b}"
            else:
                result = f"0b{v // SCALE:b}"

        else:
            sign = "-" if is_neg else ""

            # --- SCI mode (like HP42S SCI n) ---
            if display_format == "sci":
                fval = v / SCALE
                if fval == 0.0:
                    result = f"{sign}0." + "0" * DISPLAY_DIGITS + "E+00"
                else:
                    exp = math.floor(math.log10(fval))
                    mantissa_val = fval / (10 ** exp)
                    mantissa_val = round(mantissa_val, DISPLAY_DIGITS)
                    if mantissa_val >= 10:
                        mantissa_val /= 10
                        exp += 1
                    dec_str = f"{mantissa_val:.{DISPLAY_DIGITS}f}"
                    exp_sign = "+" if exp >= 0 else "-"
                    result = f"{sign}{dec_str}E{exp_sign}{abs(exp):02d}"

            # --- ENG mode (like HP42S ENG n) ---
            elif display_format == "eng":
                fval = v / SCALE
                if fval == 0.0:
                    result = f"{sign}0." + "0" * DISPLAY_DIGITS + "E+00"
                else:
                    exp = math.floor(math.log10(fval))
                    eng_exp = (exp // 3) * 3
                    mantissa_val = fval / (10 ** eng_exp)
                    mantissa_val = round(mantissa_val, DISPLAY_DIGITS)
                    if mantissa_val >= 1000:
                        mantissa_val /= 1000
                        eng_exp += 3
                    dec_str = f"{mantissa_val:.{DISPLAY_DIGITS}f}"
                    exp_sign = "+" if eng_exp >= 0 else "-"
                    result = f"{sign}{dec_str}E{exp_sign}{abs(eng_exp):02d}"

            # --- FIX (default decimal) ---
            else:
                int_part = v // SCALE
                frac_part = f"{v % SCALE:0{SCALE_POW}d}"[:DISPLAY_DIGITS].rstrip('0')
                int_str = f"{int_part:,}".replace(",", THOUSAND_SEP)
                res = int_str + (f".{frac_part}" if frac_part else "")
                if res == "" or res == ".":
                    res = "0"
                result = sign + res

    except Exception as e:
        show_error(f"Format error: {e}")
        return "Error"

    # Overflow guard: truncate with ellipsis if wider than display box
    if len(result) > MAX_DISPLAY_WIDTH:
        result = "…" + result[-(MAX_DISPLAY_WIDTH - 1):]
    return result

# Reads a single keypress from the terminal,
# handling special keys and escape sequences
# for both Windows and Unix-like systems.
def get_char():
    
    if os.name == "nt":
        ch = msvcrt.getch()

        # catch special keys (arrows, delete, etc.) which return a
        # two-character sequence starting with b'\x00' or b'\xe0'
        if ch in (b'\x00', b'\xe0'):
            special_ch = msvcrt.getch()
            #return ""
            mapping = {b'H': "UP", b'P': "DOWN", b'K': "LEFT", b'M': "RIGHT", b'S': "DEL", b'I': "PGUP", b'Q': "PGDN"}
            # 83 (b'S') is the DEL key, which sends a 2-char
            # sequence (b'\x00' or b'\xe0' followed by b'S')
            if special_ch in mapping:
                return mapping[special_ch]
            
        try:
            return ch.decode("utf-8")
        except:
            return ""

    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            
            # Check if an escape sequence starts
            if ch == '\x1b':
                # Read the next two characters (e.g., '[' and 'A')
                ch += sys.stdin.read(2)
                
                # 4-char sequences: \x1b[3~ (DEL), \x1b[5~ (PgUp), \x1b[6~ (PgDn)
                if ch.endswith(('[3', '[5', '[6')):
                    ch += sys.stdin.read(1)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# -------------------------
# About Screen
# -------------------------
def display_about():
    sys.stdout.write(HOME + CURSORHIDE + ERASEDOWN)
    print(f"{WHITE}{BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{RESET}")
    print(f"{WHITE}{BOLD}┃ ABOUT {APPNAME} {VERSION}{RESET}{WHITE}             ┃{RESET}")
    print(f"{WHITE}{BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET}")
    print(f"\n Author:       {LIGHTGRAY}{AUTHOR}{RESET}")
    print(f"\n Email:        {LIGHTGRAY}{EMAIL}{RESET}")
    print(f"\n Description:  {LIGHTGRAY}A simple yet feature-rich RPN calculator for the terminal.{RESET}")
    print(f"               {LIGHTGRAY}Written to be useful, not fancy and cluttered.{RESET}")
    print(f"\n License:      {LIGHTGRAY}GNU General Public License v3.0 or later{RESET}")
    print(f"{LIGHTGRAY}─────────────────────────────────────────────────────────────────────────{RESET}")
    # q key to return to main UI
    print(f"{FOOTER}q: quit                                                                  {RESET}")
    sys.stdout.write(CURSORSHOW)
        # Wait until 'q' is pressed
    while True:
        if get_char().lower() == 'q':
            sys.stdout.write(CLS + HOME)
            break

# -------------------------
# Help Screen
# -------------------------
def display_help():
    PAGE_SIZE = os.get_terminal_size().lines - 3
    H = f"{BOLD}{LIGHTGRAY}"
    L = LIGHTGRAY
    HELP_LINES = [
        f"{H}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{RESET}",
        f"{H}┃  HELP MENU                                              ┃{RESET}",
        f"{H}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET}",
        f"{H}── Hotkeys ────────────────────────────────────────────────{RESET}",
        f"{L} CTRL-X    : exit {APPNAME}{RESET}",
        f"{L} CTRL-L    : clears entire stack{RESET}",
        f"{L} BACKSPACE : drop stack 1{RESET}",
        f"{L} DEL       : drop stack 1{RESET}",
        f"{L} CTRL-K    : drop actual input > {RESET}",
        f"{L} TAB       : swap stack 1 and stack 2{RESET}",
        f"{L} ENTER     : duplicate stack 1 (if input is empty){RESET}",
        f"{L} CTRL-E    : edit stack 1{RESET}",
        f"{L} CTRL-N    : help{RESET}",
        f"{H}── Commands ───────────────────────────────────────────────{RESET}",
        f"{L} exit, quit, off : exit {APPNAME}{RESET}",
        f"{L} help            : show this help{RESET}",
        f"{L} about, info     : about dialog{RESET}",
        f"{L} mem             : show available mem of OS{RESET}",
        f"{L} refresh         : refresh user interface{RESET}",
        f"{H}── Instantaneous Arithmetic Operations ────────────────────{RESET}",
        f"{L} +  : addition. Returns stack 2 + stack 1{RESET}",
        f"{L} -  : subtraction. Returns stack 2 - stack 1{RESET}",
        f"{L} *  : multiplication. Returns stack 2 * stack 1{RESET}",
        f"{L} /  : division. Returns stack 2 / stack 1{RESET}",
        f"{L} %  : percentage. Returns stack 2 % stack 1{RESET}",
        f"{L} ^  : exponention (yˣ). Returns stack 2 ^ stack 1{RESET}",
        f"{L} _  : changes the sign of a number (+/-). Returns -stack 1{RESET}",
        f"{H}── Stack Operations ───────────────────────────────────────{RESET}",
        f"{L} clr                   : clear entire stack{RESET}",
        f"{L} swap                  : swap stack 2 and stack 1{RESET}",
        f"{L} drop                  : drop stack 1{RESET}",
        f"{L} drop2                 : drop stack 1 and stack 2{RESET}",
        f"{L} dup, duplicate, enter : duplicate stack 1{RESET}",
        f"{L} dup2                  : duplicate stack 1 and stack 2{RESET}",
        f"{L} edit                  : edit stack 1 (for corrections){RESET}",
        f"{L} depth                 : number of elements in stack.{RESET}",
        f"{L} avg                   : average of entire stack{RESET}",
        f"{L} save                  : save entire stack to ~/stack.txt{RESET}",
        f"{L} save {ITALIC}<filename>{RESET}{L}       : save entire stack to ~/<filename>{RESET}",
        f"{L} sort                  : sort entire stack {RESET}",
        f"{L} sum                   : sum of entire stack{RESET}",
        f"{L} rollup                : rollup entire stack{RESET}",
        f"{L} rolldown              : rolldown entire stack{RESET}",
        f"{L} over                  : copy stack 2 to stack 1 (non-destructive){RESET}",
        f"{L} pick                  : copy stack[n] to top (n from stack 1, 1-based){RESET}",
        f"{H}── Sign and basic operation ───────────────────────────────{RESET}",
        f"{L} neg, chs             : negation{RESET}",
        f"{L} abs                  : absolute value{RESET}",
        f"{L} ip, int, integer     : integer of a given value (cut){RESET}",
        f"{L} fp, frac, fractional : fractional part of a given value{RESET}",
        f"{L} mant, mantissa       : mantissa of a number{RESET}",
        f"{L} xpon                 : exponent of argument (floor of log10 of abs value){RESET}",
        f"{L} ceil                 : returns next greater integer{RESET}",
        f"{L} floor                : returns next smaller integer{RESET}",
        f"{L} mod, modulo          : modulo of two numbers in the stack{RESET}",
        f"{L} ran, rand, random    : random number (0 < x < 1){RESET}",
        f"{L} rnd, round           : Rounds number as specified in level 1{RESET}",
        f"{L} sign                 : sign of x → -1, 0, or 1{RESET}",
        f"{L} gcd                  : greatest common divisor{RESET}",
        f"{L} lcm                  : least common multiple{RESET}",
        f"{H}── Powers and roots ───────────────────────────────────────{RESET}",
        f"{L} reci, reciprocal, inv : reciproke (1/𝑥){RESET}",
        f"{L} pow, power            : exponentiation (yˣ){RESET}",
        f"{L} sq, square            : square (𝑥²){RESET}",
        f"{L} sqrt, squareroot      : square root (√𝑥){RESET}",
        f"{L} root, rt, xroot       : ⁿ√𝑥{RESET}",
        f"{L} exp                   : eˣ (inverse of ln){RESET}",
        f"{L} exp10, alog           : 10ˣ (inverse of log10){RESET}",
        f"{H}── Logarithms ─────────────────────────────────────────────{RESET}",
        f"{L} ln         : natural (base e) logarithm{RESET}",
        f"{L} log10, log : common log (base 10){RESET}",
        f"{L} log2       : logarithm base 2{RESET}",
        f"{H}── Trigonometric functions (degrees) ───────────────────────{RESET}",
        f"{L} atan2                     : atan(y/x) in degrees, stack2=y stack1=x{RESET}",
        f"{L} sin, sine                 : sine{RESET}",
        f"{L} asin, arcsine             : arc sine{RESET}",
        f"{L} sinh, sinushyperbolicus   : hyperbolic sine{RESET}",
        f"{L} cos, cosine               : cosine{RESET}",
        f"{L} acos, arccosine           : arc cosine{RESET}",
        f"{L} cosh, cosinushyperbolicus : hyperbolic cosine{RESET}",
        f"{L} tan, tangent              : tangent{RESET}",
        f"{L} atan arctangent           : arc tangent{RESET}",
        f"{L} tanh tangenthyperbolicus  : hyperbolic tangent{RESET}",
        f"{H}── Constants ──────────────────────────────────────────────{RESET}",
        f"{L} pi                 : 3.1415927… (π){RESET}",
        f"{L} tau                : 6.2831853… (𝜏 = 2π){RESET}",
        f"{L} c or lightspeed    : 299792458 m/s (𝑐){RESET}",
        f"{L} euler              : 2.7182818… (ℯ){RESET}",
        f"{L} gravity or g       : 9.80665m/s² (𝑔){RESET}",
        f"{L} phy or goldenratio : 1.6180339887… (φ = (1 + √5) / 2){RESET}",
        f"{H}── Logic ──────────────────────────────────────────────────{RESET}",
        f"{L} setwordsize or stws    : sets word size for logic ops{RESET}",
        f"{L}                          default word size is 64 bits{RESET}",
        f"{L} recallwordsize or rcws : recalls word size to stack{RESET}",
        f"{L} and                    : bitwise AND{RESET}",
        f"{L} or                     : bitwise OR{RESET}",
        f"{L} xor                    : bitwise XOR{RESET}",
        f"{L} not                    : bitwise NOT{RESET}",
        f"{L} sl or lsl              : logical shift left 1 bit{RESET}",
        f"{L} sr or lsr              : logical shift right 1 bit{RESET}",
        f"{L} slb                    : shift left 1 byte (8 bits){RESET}",
        f"{L} srb                    : shift right 1 byte (8 bits){RESET}",
        f"{L} asr                    : arithmetic shift right (sign bit replicated){RESET}",
        f"{L} rl                     : rotate left 1 bit{RESET}",
        f"{L} rr                     : rotate right 1 bit{RESET}",
        f"{L} rlb                    : rotate left 1 byte (8 bits){RESET}",
        f"{L} rrb                    : rotate right 1 byte (8 bits){RESET}",
        f"{H}── Memory ─────────────────────────────────────────────────{RESET}",
        f"{L} sto : stores stack 1 to memory{RESET}",
        f"{L} rcl : recalls stored value to stack 1{RESET}",
        f"{L} mc  : clears memory{RESET}",
        f"{H}── Display Modes ──────────────────────────────────────────{RESET}",
        f"{L} Base:    dec, hex, oct, bin{RESET}",
        f"{L} Format:  fix {ITALIC}(default){RESET}{L}, sci, eng {ITALIC}(e.g. 4 sci){RESET}",
        f"{H}── Conversions ────────────────────────────────────────────{RESET}",
        f"{L} deg2rad or d>r or deg>rad   : Degrees-to-radians conversion.{RESET}",
        f"{L} rad2deg or r>d or rad>deg   : radians → degrees{RESET}",
        f"{L} >hms or 2hms                : decimal hours → H.MMSSss{RESET}",
        f"{L} >h   or 2hours              : H.MMSSss → decimal hours{RESET}",

    ]
    # Calculate total pages and initialize page index
    total_pages = max(1, math.ceil(len(HELP_LINES) / PAGE_SIZE))
    page = 0

    def draw_page(p):
        sys.stdout.write(HOME + CURSORHIDE + ERASEDOWN)
        start = p * PAGE_SIZE
        for line in HELP_LINES[start : start + PAGE_SIZE]:
            print(line)
        if p < total_pages - 1:
            print(f"{DARKGRAY}         ↓ more ↓{RESET}")
        print(f"{WHITE}{BOLD}───────────────────────────────────────────────────────────{RESET}")
        nav = f"{FOOTER}[Page {p+1}/{total_pages}] | \u2191: up | \u2193: down | SPACE: scrolldown | q: quit{RESET}"
        sys.stdout.write(f"{WHITE}{nav}{RESET}")
        sys.stdout.flush()

    draw_page(page)
    sys.stdout.write(CURSORSHOW)

    while True:
        ch = get_char()
        if ch.lower() == 'q':
            sys.stdout.write(CLS + HOME)
            break
        elif ch in (" ", "\x1b[B", "DOWN"):
            if page < total_pages - 1:
                page += 1
                draw_page(page)
        elif ch in ("\x1b[A", "UP"):
            if page > 0:
                page -= 1
                draw_page(page)
        else:
            # show error unknown key on lowest line for 2 seconds
            print(f"{WHITE}{BOLD}\n\n\n\nUnknown key: Use arrow keys, space, or 'q' to navigate.\n\n\n\n{RESET}")
            time.sleep(2)
            # clear entire screen and redraw current page to remove error message
            sys.stdout.write(CLS + HOME)
            draw_page(page)

# -------------------------
# Text-based UI
# -------------------------
def display_ui(buffer_text):  
    sys.stdout.write(CURSORHIDE + CLEAR_SCROLLBACK + HOME)
    print(f"{LIGHTGRAY}CTRL-N for help, CTRL-X to exit{RESET}")
    print(f"{WHITE}┌──────────────────────────────────────────────┐{RESET}")
    print(f"{WHITE}│{BOLD}{WHITE}{APPNAME} {VERSION}{RESET}{WHITE}                  │{RESET}")
    print(f"{WHITE}├──────────────────────────────────────────────┤{RESET}")
    for i in range(3, -1, -1):
        val_str = format_val(stack[i]) if i < len(stack) else ""
        label = f" {i+1}: "
        display_line = "{:<4}{:>42}".format(label, val_str)
        print(f"{WHITE}│{LIGHTGRAY}{display_line}{RESET}{WHITE}│{RESET}")
    print(f"{WHITE}└──────────────────────────────────────────────┘{RESET}")
    mode_parts = []
    if display_mode != "dec":
        mode_parts.append(display_mode)
    if display_format != "fix":
        mode_parts.append(display_format)
    suffix = f" ({', '.join(mode_parts)})" if mode_parts else ""
    line = f"input{suffix} > {buffer_text}"
    sys.stdout.write(f"{ERASELINE}{WHITE}{line}{RESET}{ERASEDOWN}")

    # Cursor back to the correct position in the input buffer
    move_left = len(buffer_text) - cursor_pos
    if move_left > 0:
        sys.stdout.write(f"\x1b[{move_left}D")
    sys.stdout.write(CURSORSHOW)
    sys.stdout.flush()

# -------------------------
# Main Execution Loop
# -------------------------
input_buffer = ""
cursor_pos = 0
memory_value = 0

sys.stdout.write(CURSORHIDE)
sys.stdout.write(CLEAR_SCROLLBACK)
sys.stdout.write(CLS + HOME)

while True:
    error_displayed = False  # Reset error flag at the start of each loop
    try:
        display_ui(input_buffer)
        char = get_char()

        # --- HOTKEYS ---

        # EXIT: CTRL-X
        if char == "\x18": # CTRL-X
            print(f"\n{RESET}")
            sys.stdout.write(CURSORSHOW)
            break
            
         # HELP: CTRL-N
        elif char == "\x0e": # CTRL-N
            display_help()
            input_buffer = ""
            cursor_pos = 0
            continue
         
        # --- BACKSPACE ---
        elif (os.name == "nt" and char == "\x08") or (os.name != "nt" and char == "\x7f"):
            if cursor_pos > 0:
                input_buffer = input_buffer[:cursor_pos-1] + input_buffer[cursor_pos:]
                cursor_pos -= 1
            elif len(stack) > 0:
                stack.pop(0)
            else:
                show_error("Error: Stack 1 is empty")
            continue
            
        # SWAP: TAB
        elif char == "\t": # TAB
            if len(stack) >= 2:
                stack[0], stack[1] = stack[1], stack[0]
            else:
                show_error(f"Error: Too few arguments to swap")
            continue

        # CLEAR: CTRL-L
        elif char == "\x0c": # CTRL-L
            if len(stack) > 0:
                stack = []
                input_buffer = ""
                cursor_pos = 0
            else:
                show_error("Error: Stack is already empty")
            continue

        # DELETE: DEL key (delete character under cursor, or if at end of buffer, delete top of stack)
        elif (os.name == "nt" and char.endswith("DEL")) or (os.name != "nt" and char == "\x1b[3~"):
            if 0 <= cursor_pos < len(input_buffer):
                # Lösche das Zeichen **unter dem Cursor**
                input_buffer = input_buffer[:cursor_pos] + input_buffer[cursor_pos+1:]
            elif len(stack) > 0:
                stack.pop(0)
            else:
                show_error("Error: Stack 1 is empty")
            continue

        # CURSOR LEFT: LEFT Key (Puts the cursor one position to the left without deleting characters.)
        elif (os.name == "nt" and char == "LEFT") or (os.name != "nt" and char == "\x1b[D"):
            if cursor_pos > 0:
                cursor_pos -= 1
            continue

        # CURSOR RIGHT: RIGHT Key (Puts the cursor one position to the right without deleting characters.)
        elif (os.name == "nt" and char == "RIGHT") or (os.name != "nt" and char == "\x1b[C"):
            if cursor_pos < len(input_buffer):
                cursor_pos += 1
            continue

        # Drops input: CTRL-K
        elif char == '\x0b':
            input_buffer = ""
            cursor_pos = 0
            continue

        # Edit stack 1: CTRL-E
        elif char == '\x05':
            if len(stack) > 0:
                input_buffer = str(stack[0] // SCALE) 
                stack.pop(0)
                cursor_pos = len(input_buffer)
            else:
                show_error("Error: Stack is empty")
            continue

        # --- INSTANT NEGATE ---
        if char == "_":
            if input_buffer:
                val = to_fixed(input_buffer)
                if val is not None:
                    stack.insert(0, val)
                input_buffer = ""
                cursor_pos = 0
            if len(stack) > 0:
                stack[0] = -stack[0]
            else:
                show_error("Error: Stack 1 is empty (negate)")
            continue

        # --- INSTANT MATH OPERATORS (+, -, *, /, %, ^) ---
        if char in "+-*/%^":
            # Allow e.g. 1E-3 or 1E+6: if buffer ends with 'e', treat +/- as part of exponent
            if char in "+-" and input_buffer and input_buffer[-1].lower() == "e":
                input_buffer += char
                cursor_pos += 1
                continue
            if input_buffer:
                val = to_fixed(input_buffer)
                if val is not None:
                    stack.insert(0, val)
                input_buffer = ""
                cursor_pos = 0

            # Check if there are at least 2 values on the stack for binary operations
            if len(stack) < 2:
                show_error("Error: Too few arguments for operator")
                continue

            try:
                y, x = stack.pop(0), stack.pop(0)
                res = None
                if char == "+":
                    res = x + y
                elif char == "-":
                    res = x - y
                elif char == "*":
                    res = (x * y) // SCALE
                elif char == "/":
                    if y == 0:
                        stack.insert(0, x)
                        stack.insert(0, y)
                        show_error("Error: Division by zero")
                    else:
                        res = (x * SCALE) // y
                elif char == "%":
                    res = (x * y) // (100 * SCALE)
                elif char == "^":
                    try:
                        res = int(math.pow(x/SCALE, y/SCALE) * SCALE)
                    except ValueError as e:
                        show_error(f"Error: {e}")
                        stack.insert(0, x)
                        stack.insert(0, y)
                if res is not None:
                    stack.insert(0, res)
            except Exception as e:
                show_error(f"Operator error: {e}")

        # --- ENTER KEY (Commands, Functions, Logic) ---
        elif char in ("\r", "\n"):
            cmd = input_buffer.lower().strip()
            if not cmd:
                if len(stack) > 0: stack.insert(0, stack[0])
            elif cmd in ("exit", "quit", "off"):
                sys.stdout.write(CURSORSHOW)
                print(f"\n{RESET}")
                break
            elif cmd in ("help", "hlp", "?"): display_help()
            elif cmd in ("about", "info"): display_about()
            #refreshes the entire UI
            elif cmd == "refresh": sys.stdout.write(HOME + CURSORHIDE + ERASEDOWN)
            elif cmd in ("hex", "dec", "bin", "oct"): display_mode = cmd
            elif cmd in ("clr", "clear"): stack = []
            elif cmd in ("swap", "swp") and len(stack) >= 2:
                stack[0], stack[1] = stack[1], stack[0]
            elif cmd == "drop" and len(stack) > 0:
                stack.pop(0)
            elif cmd == "drop2" and len(stack) > 1:
                stack.pop(1) ; stack.pop(0)
            elif cmd in ("dup", "duplicate", "enter") and len(stack) > 0:
                stack.insert(0, stack[0])
            elif cmd == "dup2" and len(stack) > 1:
                stack.insert(0, stack[0]); stack.insert(3, stack[3])
            elif cmd == "over" and len(stack) >= 2:
                # OVER: copy stack 2 to stack 1 (non-destructive)
                stack.insert(0, stack[1])
            elif cmd == "pick" and len(stack) >= 2:
                # PICK: copy stack[n] to stack 1 (n from stack 1, 1-based)
                n = stack.pop(0) // SCALE
                if 1 <= n <= len(stack):
                    stack.insert(0, stack[n - 1])
                else:
                    show_error(f"Error: pick index {n} out of range")
            elif cmd == "edit":
                if len(stack) > 0:
                    input_buffer = str(stack[0] // SCALE) 
                    stack.pop(0)
                    cursor_pos = len(input_buffer)
                    continue
                else:
                    show_error("Error: Stack is empty, editing not possible")
                    continue
            elif cmd in ("fix", "sci", "eng") and len(stack) > 0:
                n = stack.pop(0) // SCALE
                if 0 <= n <= SCALE_POW:
                    DISPLAY_DIGITS = n
                    display_format = cmd
                else:
                    show_error(f"Error: invalid {cmd} digits-value {n}. Valid range is 0 to {SCALE_POW}.")
            # show how many elements in stack
            elif cmd== "depth": stack.insert(0, len(stack) * SCALE)

            elif cmd == "sto":
                if len(stack) > 0:
                    memory_value = stack.pop(0)
                else:
                    show_error("Error: Stack 1 is empty, nothing to store to memory")
            elif cmd in ("rcl","recall"):
                   stack.insert(0,memory_value)
            elif cmd in ("mc", "memclr", "mclear"):
                memory_value = 0
            elif cmd in ("chs", "neg") and len(stack) > 0: 
                stack[0] = -stack[0]
            # logical operations
            elif cmd in ("stws", "setwordsize") and len(stack) > 0:
                n = stack.pop(0) // SCALE
                if 1 <= n <= MAX_DIGITS * 4: # max 124 bits for 31 digits (with some safety margin)
                    setwordsize = n
                else:
                    show_error(f"Error: invalid word size {n}. Valid range is 1 to {MAX_DIGITS * 4} bits.")
            elif cmd in ("rcws", "recallwordsize"):
                stack.insert(0, setwordsize * SCALE)
            #logical not in dependency of setwordsize
            elif cmd == "not" and len(stack) > 0:
                mask = (1 << setwordsize) - 1
                stack[0] = ((~(stack[0] // SCALE)) & mask) * SCALE

            elif cmd in ("sl", "lsl") and len(stack) > 0:
                # SL / LSL: Shift Left 1 bit, MSB dropped, wordsize mask applied
                mask = (1 << setwordsize) - 1
                stack[0] = ((stack[0] // SCALE << 1) & mask) * SCALE
            elif cmd in ("sr", "lsr") and len(stack) > 0:
                # SR / LSR: Logical Shift Right 1 bit, MSB=0, no sign extension
                mask = (1 << setwordsize) - 1
                stack[0] = (((stack[0] // SCALE) & mask) >> 1) * SCALE
            elif cmd == "slb" and len(stack) > 0:
                # SLB: Shift Left Byte (8 bits), upper bits dropped, wordsize mask applied
                mask = (1 << setwordsize) - 1
                stack[0] = ((stack[0] // SCALE << 8) & mask) * SCALE
            elif cmd == "srb" and len(stack) > 0:
                # SRB: Shift Right Byte (8 bits), upper byte filled with 0
                mask = (1 << setwordsize) - 1
                stack[0] = (((stack[0] // SCALE) & mask) >> 8) * SCALE
            elif cmd == "asr" and len(stack) > 0:
                # ASR: Arithmetic Shift Right, sign bit (MSB within wordsize) is replicated
                mask = (1 << setwordsize) - 1
                bits = (stack[0] // SCALE) & mask
                sign_bit = (bits >> (setwordsize - 1)) & 1
                stack[0] = ((bits >> 1) | (sign_bit << (setwordsize - 1))) * SCALE
            elif cmd in ("rl", "rotl") and len(stack) > 0:
                # RL: Rotate Left 1 bit (MSB wraps to LSB)
                mask = (1 << setwordsize) - 1
                bits = (stack[0] // SCALE) & mask
                msb = (bits >> (setwordsize - 1)) & 1
                stack[0] = (((bits << 1) & mask) | msb) * SCALE
            elif cmd in ("rr", "rotr") and len(stack) > 0:
                # RR: Rotate Right 1 bit (LSB wraps to MSB)
                mask = (1 << setwordsize) - 1
                bits = (stack[0] // SCALE) & mask
                lsb = bits & 1
                stack[0] = ((bits >> 1) | (lsb << (setwordsize - 1))) * SCALE
            elif cmd == "rlb" and len(stack) > 0:
                # RLB: Rotate Left Byte (8 bits)
                mask = (1 << setwordsize) - 1
                bits = (stack[0] // SCALE) & mask
                top_byte = (bits >> (setwordsize - 8)) & 0xFF
                stack[0] = (((bits << 8) & mask) | top_byte) * SCALE
            elif cmd == "rrb" and len(stack) > 0:
                # RRB: Rotate Right Byte (8 bits)
                mask = (1 << setwordsize) - 1
                bits = (stack[0] // SCALE) & mask
                low_byte = bits & 0xFF
                stack[0] = ((bits >> 8) | (low_byte << (setwordsize - 8))) * SCALE
            elif cmd in ("and", "or", "xor") and len(stack) >= 2:
                mask = (1 << setwordsize) - 1
                y = (stack.pop(0) // SCALE) & mask
                x = (stack.pop(0) // SCALE) & mask
                if cmd == "and": stack.insert(0, (x & y) * SCALE)
                elif cmd == "or":  stack.insert(0, (x | y) * SCALE)
                elif cmd == "xor": stack.insert(0, (x ^ y) * SCALE)
            elif cmd in ("sq", "square") and len(stack) > 0:
                stack[0] = (stack[0] * stack[0]) // SCALE
            elif cmd in ("sqrt", "squareroot") and len(stack) > 0:
                if stack[0] < 0: show_error("Error: Negative Square Root")
                else: stack[0] = int(math.sqrt(stack[0] / SCALE) * SCALE)
            elif cmd in ("root", "rt", "xroot") and len(stack) >= 2:
                stack[1] = int((stack[1]/SCALE) ** (1/(stack[0]/SCALE)) * SCALE); stack.pop(0)
            elif cmd in ("pow", "power") and len(stack) >= 2:
                stack[1] = int(math.pow(stack[1]/SCALE, stack[0]/SCALE) * SCALE); stack.pop(0)
            elif cmd in ("reci", "inv", "reciprocal") and len(stack) > 0:
                if stack[0] == 0: show_error("Error: Div/0")
                else: stack[0] = (SCALE * SCALE) // stack[0]
            elif cmd in ("abs", "absolute") and len(stack) > 0:
                stack[0] = abs(stack[0])
            elif cmd in ("ip", "int", "integer") and len(stack) > 0:
                stack[0] = (stack[0] // SCALE) * SCALE
            elif cmd in ("fp", "frac", "fractional") and len(stack) > 0:
                stack[0] = stack[0] % SCALE
            
            elif cmd in ("mant", "mantissa") and len(stack) > 0:
                if stack[0] == 0:
                    stack[0] = 0
                else:
                    exponent = math.floor(math.log10(abs(stack[0] / SCALE)))
                    stack[0] = int((stack[0] / (10 ** exponent)) * SCALE)
            elif cmd == "floor" and len(stack) > 0:
                stack[0] = math.floor(stack[0] / SCALE) * SCALE
            elif cmd == "ceil" and len(stack) > 0:
                stack[0] = math.ceil(stack[0] / SCALE) * SCALE
            elif cmd in ("mod", "modulo") and len(stack) >= 2:
                y, x = stack.pop(0), stack.pop(0)
                if y == 0:
                    stack.insert(0, x); stack.insert(0, y)
                    show_error("Error: Div/0")
                else:
                    stack.insert(0, (x % y) // SCALE * SCALE)
            elif cmd == "pi": stack.insert(0, PI_INT)
            elif cmd == "euler": stack.insert(0, E_INT)
            elif cmd == "gravity": stack.insert(0, G_INT)
            elif cmd in ("phi", "goldenratio"): stack.insert(0, PHI_INT)
            elif cmd == "lightspeed": stack.insert(0, C_INT)
            elif cmd == "tau": stack.insert(0, TAU_INT)
            elif cmd in ("sin", "sine") and len(stack) > 0:
                stack[0] = int(math.sin(math.radians(stack[0]/SCALE)) * SCALE)
            elif cmd in ("asin", "arcsin") and len(stack) > 0:
                stack[0] = int(math.degrees(math.asin(stack[0]/SCALE)) * SCALE)
            elif cmd in ("sinh", "sinushyperbolicus") and len(stack) > 0:
                stack[0] = int(math.sinh(stack[0]/SCALE) * SCALE)
            elif cmd in ("cos", "cosine") and len(stack) > 0:
                stack[0] = int(math.cos(math.radians(stack[0]/SCALE)) * SCALE)
            elif cmd in ("acos", "arccos") and len(stack) > 0:
                stack[0] = int(math.degrees(math.acos(stack[0]/SCALE)) * SCALE)
            elif cmd in ("cosh", "cosinushyperbolicus") and len(stack) > 0:
                stack[0] = int(math.cosh(stack[0]/SCALE) * SCALE)
            elif cmd in ("tan", "tangent") and len(stack) > 0:
                stack[0] = int(math.tan(math.radians(stack[0]/SCALE)) * SCALE)
            elif cmd in ("atan", "arctan") and len(stack) > 0:
                stack[0] = int(math.degrees(math.atan(stack[0]/SCALE)) * SCALE)
            elif cmd in ("tanh", "tangenthyperbolicus") and len(stack) > 0:
                stack[0] = int(math.tanh(stack[0]/SCALE) * SCALE)
            elif cmd == "ln" and len(stack) > 0:
                if stack[0] <= 0: show_error("Error: Log Range")
                else: stack[0] = int(math.log(stack[0]/SCALE) * SCALE)
            elif cmd in ("log10", "log") and len(stack) > 0:
                if stack[0] <= 0: show_error("Error: Log Range")
                else: stack[0] = int((math.log(stack[0]/SCALE) / math.log(10)) * SCALE)
            elif cmd == "log2" and len(stack) > 0:
                if stack[0] <= 0: show_error("Error: Log Range")
                else: stack[0] = int((math.log(stack[0]/SCALE) / math.log(2)) * SCALE)
            elif cmd == "exp" and len(stack) > 0:
                stack[0] = int(math.exp(stack[0]/SCALE) * SCALE)
            elif cmd in ("exp10", "alog") and len(stack) > 0:
                stack[0] = int((10 ** (stack[0]/SCALE)) * SCALE)
            elif cmd == "sign" and len(stack) > 0:
                v = stack[0]
                stack[0] = (1 if v > 0 else -1 if v < 0 else 0) * SCALE
            elif cmd == "xpon" and len(stack) > 0:
                # XPON: exponent of argument (floor of log10 of abs value)
                v = abs(stack[0] / SCALE)
                if v == 0: show_error("Error: Exponent undefined for 0")
                else: stack[0] = int(math.floor(math.log10(v))) * SCALE
            elif cmd == "gcd" and len(stack) >= 2:
                a, b = abs(stack.pop(0) // SCALE), abs(stack.pop(0) // SCALE)
                stack.insert(0, math.gcd(a, b) * SCALE)
            elif cmd == "lcm" and len(stack) >= 2:
                a, b = abs(stack.pop(0) // SCALE), abs(stack.pop(0) // SCALE)
                stack.insert(0, (a * b // math.gcd(a, b) if math.gcd(a, b) else 0) * SCALE)
            elif cmd == "atan2" and len(stack) >= 2:
                # atan2(y, x): stack 2 = y, stack 1 = x → angle in degrees
                x, y = stack.pop(0), stack.pop(0)
                stack.insert(0, int(math.degrees(math.atan2(y/SCALE, x/SCALE)) * SCALE))
            elif cmd in ("deg2rad", "d>r", "deg>rad") and len(stack) > 0:
                stack[0] = int(math.radians(stack[0]/SCALE) * SCALE)
            elif cmd in ("rad2deg", "r>d", "rad>deg") and len(stack) > 0:
                stack[0] = int(math.degrees(stack[0]/SCALE) * SCALE)
            elif cmd in ("2hms", ">hms") and len(stack) > 0:
                # decimal hours → H.MMSSss  e.g. 1.5 → 1.3000 (1h30m00s)
                h_dec = stack[0] / SCALE
                sign = -1 if h_dec < 0 else 1
                h_dec = abs(h_dec)
                h = int(h_dec)
                m = int((h_dec - h) * 60)
                s = ((h_dec - h) * 60 - m) * 60
                stack[0] = sign * int((h + m/100 + s/10000) * SCALE)
            elif cmd in ("2hours", ">h", "hms>h") and len(stack) > 0:
                # H.MMSSss → decimal hours  e.g. 1.3000 → 1.5
                hms = stack[0] / SCALE
                sign = -1 if hms < 0 else 1
                hms = abs(hms)
                h = int(hms)
                m = int(round((hms - h) * 100))
                s = round(((hms - h) * 100 - m) * 100, 6)
                stack[0] = sign * int((h + m/60 + s/3600) * SCALE)
            elif cmd in ("ran", "rand", "random"): stack.insert(0, int(random.random() * SCALE))
            elif cmd in ("round", "rnd") and len(stack) >= 2:
                stack[1] = int(round(stack[1]/SCALE, stack[0]//SCALE) * SCALE); stack.pop(0)
            elif cmd in ("avg", "average") and len(stack) >= 2:
                total = sum(stack[i] for i in range(min(len(stack), 10)))
                count = min(len(stack), 10)
                stack.insert(0, total // count)
            # sort entire stack in ascending order and if already, in descending order
            elif cmd == "sort":
                if len(stack) > 1:
                    if all(stack[i] <= stack[i+1] for i in range(len(stack)-1)):
                        stack.sort(reverse=True)
                    else:
                        stack.sort()
                else:
                    show_error("Error: nothing to sort here")
            # save stack
            #   - save entire stack as values in a text file. 
            #   - Default path is home directory with filename "stack.txt". This can be
            #     changed by providing a filename after the "save" command, e.g. "save mystack.txt".
            #   - If the file already exists, it will be overwritten.
            elif cmd.startswith("save"):
                parts = cmd.split(maxsplit=1)
                # default path is always home, either for provided filename or default "stack.txt"
                filename = os.path.expanduser(f"~/{parts[1]}") if len(parts) > 1 else os.path.expanduser("~/stack.txt")
                #filename = parts[1] if len(parts) > 1 else os.path.expanduser("~/stack.txt")
                try:
                    with open(filename, "w") as f:
                        for i in range(min(len(stack), 10)):
                            val = stack[i]
                            sign = "-" if val < 0 else ""
                            abs_val = abs(val)
                            whole = abs_val // SCALE
                            frac = abs_val % SCALE
                            if frac == 0:
                                f.write(f"{sign}{whole}\n")
                            else:
                                frac_str = f"{frac:0{SCALE_POW}d}".rstrip("0")
                                f.write(f"{sign}{whole}.{frac_str}\n")
                    print(f"\n{WHITE}Stack saved to: {filename}{RESET}")
                    time.sleep(3)
                except Exception as e:
                    show_error(f"Error saving stack: {e}")
            
            elif cmd == "sum" and len(stack) > 0:
                total = sum(stack)
                stack.insert(0, total)
            elif cmd in ("rollup", "rup"):
                if len(stack) < 2:
                    show_error("Error: Too few arguments")
                else:
                    # Take the last element and insert it at the front (Level 1)
                    bottom_item = stack.pop(-1)
                    stack.insert(0, bottom_item)                
            elif cmd in ("rolldown", "rdn", "rd"):
                if len(stack) < 2:
                    show_error("Error: Too few arguments")
                else:
                    # Take the first element and append it to the end
                    top_item = stack.pop(0)
                    stack.append(top_item)
            # return available memory of the system in bytes and remember SCALE for correct display
            elif cmd in ("memory", "mem"): 
                if sys.platform == "win32":
                    import psutil
                    mem = psutil.virtual_memory()
                    stack.insert(0, int(mem.available * SCALE))
                elif sys.platform == "linux":
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemAvailable:"):
                                mem_kb = int(line.split()[1])
                                stack.insert(0, mem_kb * 1024 * SCALE)
                                break
                else:
                    show_error("Error: Memory info not supported on this platform")

            else:
                val = to_fixed(cmd)
                if val is not None:
                    stack.insert(0, val)
                elif cmd:
                    show_error(f"Error: Unknown command or invalid value '{cmd}'")
            input_buffer = ""
            cursor_pos = 0

        # --- FILL BUFFER ---
        else:
            if char.isprintable():
                input_buffer = input_buffer[:cursor_pos] + char + input_buffer[cursor_pos:]
                cursor_pos += 1

    except Exception as e:
        show_error(f"Fatal Error: {e}")
        input_buffer = ""
        cursor_pos = 0
