CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -pthread
SRCDIR  = src
BINDIR  = bin
COMMON  = $(SRCDIR)/common.c

all: $(BINDIR)/server $(BINDIR)/client

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/server: $(SRCDIR)/server.c $(COMMON) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ $(SRCDIR)/server.c $(COMMON)

$(BINDIR)/client: $(SRCDIR)/client.c $(COMMON) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ $(SRCDIR)/client.c $(COMMON)

clean:
	rm -rf $(BINDIR)

.PHONY: all clean
