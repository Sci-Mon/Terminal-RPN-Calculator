---
title: Terminal RPN Calculator
subtitle: "an RPN calculator for the shell"
author: Simon Widmer
date: 30.03.2026
lang: en
license: GNU GPL3
cover-image: rpn-calc.svg
description: "an RPN calculator for the shell"
---

# Terminal RPN Calculator

## ![RPN CALC LOGO](rpn-calc.svg)

an RPN calculator for the shell

---

## Preface and history 📜

First of all: This calculator is not another exactly emulated Hewlett Packard ™ calculator nor is it using ROM files to provide the full functionality. At the current state, it is not able to store and execute [RPL](https://en.wikipedia.org/wiki/RPL_(programming_language))-programs. Even so, if you are used to those calculators, you might remember and recognize the most useful [commands](https://literature.hpcalc.org/community/hp48sx-qrg-en.pdf).
Lets say, the calculator mimics its great predecessors. In addition to the usual abbreviated commands, these can also be written as full words.

I am using RPN calculators since I was a teenager and still appreciate it. Hence, it is my intention to program a calculator which supports RPN (reverse polish notation) on the one hand and is executable in a terminal on the other hand. It is written in pure python and designed to be a simple and distraction free terminal shell tool with no dependencies. (Actually, this calculator has come a long way: I originally planned to create a pure Bash implementation using `bc` in the background, but ultimately decided against it during the implementation process.)

Again, keep in mind: This is not the real and famous HP42S™ or HP48SX™ that is supporting programming, unit conversions, graphs, equation solvers, libraries and lots of things I do not even know of. Those real calculators are an industrial work of art and may never be compared with.

## Installation 📦

### Linux installation 🐧

* Run `sudo apt install python3` for Debian. Installation for other distributions may vary. There is no other dependencies.
* run `./rpn.py` to start the calculator 🚀

### Windows installation 🪟️

* install [python](https://www.python.org/downloads/windows/) (Tested with Windows 11 only)
* use `run.bat` to start the calculator or open a cmd-shell and execute `py ./rpn.py` 🚀

## Usage 💡

### Disclaimer ⚠️

Don't use this calculator if you plan to fly to the moon. I'm not kidding — expect that some results might be wrong.

### General 👆

* If you are not familiar with rpn calculators and with [reverse polish notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation), you might not want to learn this notation unless you know the advantage of this concept and are willing to rethink.
* Typing in either small or capital letters is valid.
* Errors are shown in red and cleared after 2 seconds.
* Decimal numbers are separated by a period.
* the size of the stack is unlimited (in theory).

### User Interface ⎚

```text
CTRL-N for help, CTRL-X to exit
┌──────────────────────────────────────────────┐
│Terminal RPN Calculator vX.x                  │
├──────────────────────────────────────────────┤
│ 4:                                           │
│ 3:                                         64│
│ 2:                                        100│
│ 1:                                      45054│
└──────────────────────────────────────────────┘
input > ▒
```

Example Text User interface above with some numbers entered in the visible stack and cursor after input.

### Hotkeys ⌨️

* CTRL-X → exit
* CTRL-L → clears
* BACKSPACE →drop stack 1
* DEL → drop stack 1
* CTRL-K → drop actual input >
* TAB → swap stack 1 and stack 2
* ENTER → duplicate stack 1 (if input is empty)
* CTRL-E → edit stack 1
* CTRL-N → help

**Hint (ℹ):** If a hotkey is not working, this is most likely due to the terminal shell in use and it's predefined hotkeys. Workaround: enter the according command at the input prompt and hit *ENTER*.

### Commands ⚡

#### Info about commands 📝️

commands are executed by typing in and hit *ENTER*. This might feel rather like a shell therefore.

* Advantages:
  * no polling for keys but just waiting for input.
    * No CPU usage at this point.
    * Simple Code.
    * shell feeling
    * commands should be mostly the sames as the commands of RPN calculators
    * easy to memorize
  * Disadvantages:
    * typing commands for a calculator might feel unusual at first

#### General commands 📢️

* `exit`or `quit` or just `off` followed by hitting the *ENTER*-key to leave the rpn calculator.
* `help` or `hlp` to get a quite detailed help.
* `about` or `info` to get a little bit info about myself, the calculator and the license
* `refresh` to clear a destroyed UI.
* hitting the *ENTER*-key, the stack 1 value in the stack gets duplicated.
* hitting the *ENTER*-key after a command is performing it.

#### Stack commands

* `clr` or `clear` will clear the entire stack.
* `swap` will swap stack 1 and 2.
* `drop` will delete stack 1.
* `drop2` will delete stack 1 and stack 2.
* `dup` or `duplicate` or `enter` will duplicate stack 1
* `dup2` will duplicate stack1 and stack 2
* `edit` to edit stack 1
* `depth` → number of elements in stack.
* `avg` or `average` → average of entire stack.
* `sum` → sum of entire stack.
* `rollup` → Moves the very last element of the stack to Level 1 (Bottom to Top).
* `rolldown` → Moves the element from Level 1 to the very bottom of the stack (Top to Bottom).
* `over` → copies stack 2 to stack 1 (without deleting stack 1).
* `pick` → copy stack[n] to top (n from stack 1, 1-based)

#### Basic Arithmetic Operations ∑

As with the real rpn calculators, hitting the operators does execute an *immediate* operation. You do NOT have to hit the *ENTER*-key to do so.

* `+` → addition
* `-` → subtraction
* `*` → multiplication
* `/` → division
* `%` → percentage
* `^` → exponentiation (yˣ)
* `_` → changes the sign of a number (+/-)

#### Math functions ƒ(𝑥)

The following functions can be used followed by hitting *ENTER*:

* Sign and basic operation
  * `neg` or `chs` → negation
  * `abs`→ absolute value
  * `ip` or `int` or `integer` → integer of a given value (by cutting, not rounding)
  * `ceil` → returns next greater integer
  * `floor` → returns next smaller integer
  * `mod` or `modulo` → returns modulo of two numbers in the stack
  * `ran` `rand` or `random` → returns random number `0 < x < 1`
  * `rnd` or `round` → Rounds number as specified in level 1.
  * `sign` → sign of x → -1, 0, or 1
  * `gcd` → greatest common divisor
  * `lcm` → least common multiple
* Powers and roots
  * `reci` or `reciprocal` or `inv` → reciproke (1/𝑥)
  * `pow`or `power` → exponentiation (yˣ)
  * `sq` or `square` → square (𝑥²)
  * `sqrt` or `squareroot` → square root (√𝑥)
  * `root` or `rt` or `xroot` → ⁿ√𝑥
  * `exp` → eˣ (inverse of ln)
  * `exp10` or `alog` → 10ˣ (inverse of log10)
* Logarithms
  * `ln`  → natural (base e) logarithm
  * `log10` or `log` → common logarithm (base 10)
  * `log2` → binary logarithm (base 2)
* Trigonometric functions (degrees)
  * `sin` or `sine` → sine
  * `asin` or `arcsine` → arc sine
  * `sinh` or `sinushyperbolicus` → hyperbolic sine
  * `cos` or `cosine` → cosine
  * `acos` or `arccosine`→ arc cosine
  * `cosh` or `cosinushyperbolicus` → hyperbolic cosine
  * `tan` or `tangent` → tangent
  * `atan` `arctangent` → arc tangent
  * `tanh` `tangenthyperbolicus` → hyperbolic tangent

* Logic operations
  * `setwordsize` or `stws` → sets word size for logic ops (the default word size is 64 bits)
  * `recallwordsize` or `rcws` → recalls word size to stack
  * `and` → Logical or binary AND.
  * `or` → Logical or binary OR
  * `xor` → Logical or binary exclusive OR.
  * `not` → Logical or binary NOT.
  * `sl` or `lsl` → logical shift left 1 bit
  * `sr` or `lsr` → logical shift right 1 bit
  * `slb` → shift left 1 byte (8 bits)
  * `srb` → shift right 1 byte (8 bits)
  * `asr` → arithmetic shift right (sign bit replicated)
  * `rl` → rotate left 1 bit
  * `rr` → rotate right 1 bit
  * `rlb` → rotate left 1 byte (8 bits)
  * `rrb` → rotate right 1 byte (8 bits)

#### Constants ◆

The following constants are implemented for now and can be entered followed by hitting *ENTER*:

* `pi` : 3.1415927… (π)
* `tau`: 6.2831853… (𝜏 = 2π)
* `c` or `lightspeed`: 299792458 m/s (𝑐)
* `euler` : 2.7182818… (ℯ)
* `gravity` or `g`: 9.80665m/s² (𝑔)
* `phy`or `goldenratio`: 1.6180339887… (φ = (1 + √5) / 2)

#### Memory commands

* `mem` or `memory` → shows all available memory of the OS, if supported.
* `sto` or `store` will store value of stack 1 into memory and delete the value in the stack.
* `rcl` or `recall` will recall value from memory and append it to the stack. Memory contains `0` by default.
* `mc` or `memclr` or `mclear` will clear the memory and set it to `0`.

### Modes

#### Display Modes ⚙️

* `fix` → Fixed-Decimal (default), will set and show `n` display digits by the stack 1 value.
    E.g. `3 *ENTER* fix *ENTER*` will limit to 3 digits. Allowed value is `0-16`
* `eng` → Engineering notation, will set and show `n` display digits by the stack 1 value
* `sci` → Scientific notation, will set and show `n` display digits by the stack 1 value

#### Base Modes ⚙️

* `dec` will show the stack in *decimal* values
  * notation of exponential numbers: (e.g. 3e6, 1.5E4, 5.2e-3, …)
* `hex` will show the stack in *hexadecimal* values
* `bin` will show the stack in *binary* values
* `oct` will show the stack in *octal* values
* the current mode is indicated below the stack at the input prompt if not in *decimal-mode*

#### Notation of hex or bin value(s) ✒️

The notation of a hexadecimal or binary number can be typed in as follows:

* binary: e.g.: `0b1111`, `0b10101010`, …
* hexadecimal : e.g. like `0xabcd`, `0xAFAEBD`, … or directly without leading 0b or 0x.

Further notice:

* **Mixing decimal, hexadecimal and binary values in the stack is not possible.**
* if in decimal mode, all entered values with leading `0x`, `0b` or `0o` are directly converted into the decimal value.
* same behavior and conversion for the other modes

### Limitations ▲/▼

* the digits are limited to the value **`16`**.

I'm developing this pocket calculator in my spare time, so you'll notice that many features and functions — such as the following — are missing:

* programming
* matrix
* plotting
* variables
* Equation solving
* arrays
* complex number handling
* Unit conversion
* IO and many other fancy features
* small subset of hotkeys — Esc-Key and F-Keys are non-functional

For the moment, I do not have intentions to implement these features. There might be other apropriate tools to use.

### To Do's 🚧

The following features are on my to do list:

* rad, deg, (grad: not useful)
* thousands-separator: ‘,‘ or ‘'‘
* missing commands
  * asr, asl: arithmetic shift left
  * beep
  * bytes
  * date and time functions (date, date+, ddays)
  * hms
  * dropn
  * dupn,
  * fp: Returns fractional part of a number
  * key (would be nice for debugging new hotkeys)
  * lnp1 Natural logarithm of (x + 1).
  * mant mantissa
  * max, min, maxr
  * rl, rlb, rr, rrb
  * sign
  * sto+-/*
  * xpon

## Error reporting 🐛

Since I am not a deeply experienced Python programmer, errors and bugs are possibly included.
Error reports or corrections are welcome:
[sery(at)solnet.ch](mailto:sery&#x40;solnet.ch)
