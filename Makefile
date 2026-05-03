# Variablen
SOURCE_MD  = README.md
SOURCE_PY  = rpn.py
TARGET_MAN = rpn.1
INSTALL_BIN = /usr/local/bin/rpn
INSTALL_MAN = /usr/local/share/man/man1/rpn.1

# Default target: Generate man page
all: $(TARGET_MAN)

# Converting Markdown to a man page
$(TARGET_MAN): $(SOURCE_MD)
	#pandoc --standalone --to man $(SOURCE_MD) -o $(TARGET_MAN)
	sed 's/!\[.*\](.*)//g' $(SOURCE_MD) | pandoc --ascii -s -f markdown -t man -o $(TARGET_MAN)


# Installation
install: $(TARGET_MAN)
	@echo "installing executable file..."
	install -Dm755 $(SOURCE_PY) $(INSTALL_BIN)
	@echo "installing man page..."
	install -Dm644 $(TARGET_MAN) $(INSTALL_MAN)
	@echo "installation finished"

# Uninstallation
uninstall:
	rm -f $(INSTALL_BIN)
	rm -f $(INSTALL_MAN)

# Cleaning up
clean:
	rm -f $(TARGET_MAN)

.PHONY: all install uninstall clean
