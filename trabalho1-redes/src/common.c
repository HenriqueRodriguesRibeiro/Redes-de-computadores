#include "common.h"
#include "protocol.h"

#include <unistd.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <errno.h>

int send_all(int sockfd, const void *buf, size_t len) {
    const char *p = (const char *)buf;
    size_t total = 0;
    while (total < len) {
        ssize_t n = send(sockfd, p + total, len - total, 0);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        if (n == 0) return -1;
        total += (size_t)n;
    }
    return 0;
}

int recv_all(int sockfd, void *buf, size_t len) {
    char *p = (char *)buf;
    size_t total = 0;
    while (total < len) {
        ssize_t n = recv(sockfd, p + total, len - total, 0);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        if (n == 0) return -1;
        total += (size_t)n;
    }
    return 0;
}

ssize_t recv_line(int sockfd, char *line, size_t maxlen) {
    size_t i = 0;
    char c;
    while (i < maxlen - 1) {
        ssize_t n = recv(sockfd, &c, 1, 0);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        if (n == 0) break;
        if (c == '\n') break;
        if (c == '\r') continue;
        line[i++] = c;
    }
    line[i] = '\0';
    return (ssize_t)i;
}

int send_file(int sockfd, int fd_file, long filesize) {
    char buf[BUFFER_SIZE];
    long remaining = filesize;
    while (remaining > 0) {
        size_t chunk = (remaining < (long)sizeof(buf)) ? (size_t)remaining : sizeof(buf);
        ssize_t r = read(fd_file, buf, chunk);
        if (r < 0) { if (errno == EINTR) continue; return -1; }
        if (r == 0) break;
        if (send_all(sockfd, buf, (size_t)r) < 0) return -1;
        remaining -= r;
    }
    return (remaining == 0) ? 0 : -1;
}

int recv_file(int sockfd, int fd_file, long filesize) {
    char buf[BUFFER_SIZE];
    long remaining = filesize;
    while (remaining > 0) {
        size_t chunk = (remaining < (long)sizeof(buf)) ? (size_t)remaining : sizeof(buf);
        ssize_t n = recv(sockfd, buf, chunk, 0);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        if (n == 0) return -1;
        ssize_t written = 0;
        while (written < n) {
            ssize_t w = write(fd_file, buf + written, n - written);
            if (w < 0) { if (errno == EINTR) continue; return -1; }
            written += w;
        }
        remaining -= n;
    }
    return 0;
}

long file_size(const char *path) {
    struct stat st;
    if (stat(path, &st) < 0) return -1;
    if (!S_ISREG(st.st_mode)) return -1;
    return (long)st.st_size;
}
