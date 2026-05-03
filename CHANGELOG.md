# Changelog

## v1.8.1

* introduction of minor versions
* introduction of `make` as installer with a simple `Makefile`
* man page by the help of pandoc and `make`
* chapter *special thanks* in *README.md*
* temperature conversions
* command `getkey` to check the key code (used for debugging purposes only)
* command `perm` or `permutation(s)` to calculate the number of permutations of two numbers in the stack (nPr)
* command `comb` or `combination(s)` to calculate the number of combinations of two numbers in the stack (nCr)
* command `swp` or `x<>y` to swap stack 1 and stack 2 (added additionally to the already existing `swap` command)

## v1.8

* major code restructuring: This calculator has grown up since the in initial release and the code was
  getting more and more messy and unreadable. Still, it is spaghetti code with all its if's and elseif's and should be improved urgently although it is working stable.
* created Make file to install rpn-calc and a man page.
* various length conversions
* notation with exponential numbers corrected (e.g. 3e6, 1.5E4, 5.2e-3, 1E+6, 3E-5 …)
* bugfix `edit` and CTRL-E now work as expected
* Changed font "Quicksand Medium" in `rpn-calc.svg` into objects so the  appearance remains the same on all platforms without having this font installed.
* created the first binaries stored under `bin/` for Windows.
* defined ? as hotkey for help instead of a command.
* new function `alog` for common (base 10) antilogarithm (10ˣ)
* new function `expm` for eˣ - 1 (more accurate for small x)
* instant operator for division is now also ":" in addition to "/"
* changed color behaviour: stack numbering is "lightgrey" now and stack entries are bright white. (seems to work only within windows command shell)

## v1.7

* improved general error handling and used meaningful error messages
* `sort` command to sort entire stack in ascending order and if already, in descending order
* `save` command to save entire stack to ~/stack.txt in decimal values

## v1.6

* more detailed help supporting full terminal size
* `_`  to instantly neg stack 1
* implemented logic operations
* corrected and implemented further logic functions
* scientific notation for input (e.g. 3e6, 1.5E4)
* conversions between decimal hours and H.MMSSss (e.g. 1.5 → 1.3000 and 1.3000 → 1.5)
* conversions between degrees and radians (e.g. 180 → 3.1415927… and 3.1415927… → 180)

## v1.5

* Thousand separators
* ENG and SCI mode in addition to FIX
* handling of UI overflow
* paged and pimped up help
* new commands
  * `dup` to duplicate stack 1: as with ENTER
  * `edit` to edit stack 1
* new hotkeys
  * CTRL-K to drop the actual input
  * CTRL-E to edit stack 1

## v1.4

* Proper DEL and ARROW Key handling under Linux
* pimped up README.md with Unicode Symbols for easier reading

## v1.3

* implemented octal mode.
* more functions.
  * fix: define a specific amount of shown digits at runtime
* terminal buffer is cleared after the start of the calculator.
* put README.md up to date
* created svg-icon rpn-calc.svg

## v1.2

* Implemented brief help

## v1.1

* Made the calculator run under Windows that is not supporting the
  termios library.
* Supporting hotkeys

## v1.0, 09.02.2026, Initial Release

first functional version
