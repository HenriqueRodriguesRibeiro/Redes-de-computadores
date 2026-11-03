#ifndef COMMON_H
#define COMMON_H

#include <stddef.h>
#include <sys/types.h>

int send_all(int sockfd, const void *buf, size_t len);
int recv_all(int sockfd, void *buf, size_t len);
ssize_t recv_line(int sockfd, char *line, size_t maxlen);
int send_file(int sockfd, int fd_file, long filesize);
int recv_file(int sockfd, int fd_file, long filesize);
long file_size(const char *path);

#endif /* COMMON_H */
