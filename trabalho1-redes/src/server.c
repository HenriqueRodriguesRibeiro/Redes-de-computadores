#include "protocol.h"
#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <errno.h>
#include <signal.h>

static char g_basedir[MAX_PATH_LEN] = ".";

static int build_safe_path(const char *path, char *out, size_t outlen) {
    if (strstr(path, "..") != NULL) return -1;
    const char *p = path;
    while (*p == '/') p++;
    int n = snprintf(out, outlen, "%s/%s", g_basedir, p);
    if (n < 0 || (size_t)n >= outlen) return -1;
    return 0;
}

static void send_status(int cfd, int code) {
    char line[MAX_LINE_LEN];
    int n = snprintf(line, sizeof(line), "%d %s\r\n", code, status_message(code));
    send_all(cfd, line, (size_t)n);
}

static void handle_get(int cfd, const char *path) {
    char fullpath[MAX_PATH_LEN];
    if (build_safe_path(path, fullpath, sizeof(fullpath)) < 0) {
        send_status(cfd, ST_BAD_REQUEST); send_all(cfd, "\r\n", 2); return;
    }
    long fsize = file_size(fullpath);
    if (fsize < 0) { send_status(cfd, ST_NOT_FOUND); send_all(cfd, "\r\n", 2); return; }
    int fd = open(fullpath, O_RDONLY);
    if (fd < 0) {
        send_status(cfd, (errno == EACCES) ? ST_FORBIDDEN : ST_INTERNAL);
        send_all(cfd, "\r\n", 2); return;
    }
    char header[MAX_LINE_LEN];
    int n = snprintf(header, sizeof(header), "%d %s\r\n%s %ld\r\n\r\n",
                     ST_OK, status_message(ST_OK), HDR_LENGTH, fsize);
    if (send_all(cfd, header, (size_t)n) == 0) send_file(cfd, fd, fsize);
    close(fd);
    printf("[GET] %s (%ld bytes) enviado\n", fullpath, fsize);
}

static void handle_put(int cfd, const char *path, long length) {
    char fullpath[MAX_PATH_LEN];
    if (build_safe_path(path, fullpath, sizeof(fullpath)) < 0 || length < 0) {
        send_status(cfd, ST_BAD_REQUEST); send_all(cfd, "\r\n", 2); return;
    }
    int fd = open(fullpath, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        send_status(cfd, (errno == EACCES) ? ST_FORBIDDEN : ST_INTERNAL);
        send_all(cfd, "\r\n", 2); return;
    }
    if (recv_file(cfd, fd, length) < 0) {
        close(fd); send_status(cfd, ST_INTERNAL); send_all(cfd, "\r\n", 2); return;
    }
    close(fd);
    send_status(cfd, ST_CREATED); send_all(cfd, "\r\n", 2);
    printf("[PUT] %s (%ld bytes) recebido\n", fullpath, length);
}

static void *handle_client(void *arg) {
    int cfd = *(int *)arg;
    free(arg);
    char reqline[MAX_LINE_LEN];
    ssize_t r = recv_line(cfd, reqline, sizeof(reqline));
    if (r <= 0) { close(cfd); return NULL; }
    char method[16], path[MAX_PATH_LEN];
    if (sscanf(reqline, "%15s %1023s", method, path) != 2) {
        send_status(cfd, ST_BAD_REQUEST); send_all(cfd, "\r\n", 2);
        close(cfd); return NULL;
    }
    if (strcmp(method, METHOD_GET) == 0) {
        char tmp[MAX_LINE_LEN];
        recv_line(cfd, tmp, sizeof(tmp));
        handle_get(cfd, path);
    } else if (strcmp(method, METHOD_PUT) == 0) {
        char lenline[MAX_LINE_LEN]; long length = -1;
        recv_line(cfd, lenline, sizeof(lenline));
        sscanf(lenline, "%*s %ld", &length);
        char blank[MAX_LINE_LEN];
        recv_line(cfd, blank, sizeof(blank));
        handle_put(cfd, path, length);
    } else {
        send_status(cfd, ST_BAD_REQUEST); send_all(cfd, "\r\n", 2);
    }
    close(cfd);
    return NULL;
}

int main(int argc, char *argv[]) {
    int port = DEFAULT_PORT;
    if (argc >= 2) port = atoi(argv[1]);
    if (argc >= 3) {
        strncpy(g_basedir, argv[2], sizeof(g_basedir) - 1);
        g_basedir[sizeof(g_basedir) - 1] = '\0';
    }
    mkdir(g_basedir, 0755);
    signal(SIGPIPE, SIG_IGN);
    int sfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sfd < 0) { perror("socket"); exit(1); }
    int opt = 1;
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);
    if (bind(sfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) { perror("bind"); exit(1); }
    if (listen(sfd, MAX_BACKLOG) < 0) { perror("listen"); exit(1); }
    printf("Servidor ouvindo na porta %d | diretorio base: %s\n", port, g_basedir);
    while (1) {
        struct sockaddr_in cli; socklen_t clilen = sizeof(cli);
        int *cfd = malloc(sizeof(int));
        if (!cfd) continue;
        *cfd = accept(sfd, (struct sockaddr *)&cli, &clilen);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        if (pthread_create(&tid, NULL, handle_client, cfd) != 0) {
            close(*cfd); free(cfd); continue;
        }
        pthread_detach(tid);
    }
    close(sfd);
    return 0;
}
