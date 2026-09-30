#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DB_FILE "students_db.txt"
#define MAX_LINE 256

void list_students() {
    FILE *file = fopen(DB_FILE, "r");
    if (!file) {
        printf("Error: Gagal membuka berkas basis data.\n");
        return;
    }
    char line[MAX_LINE];
    printf("\n=== DAFTAR MAHASISWA (LEGACY ENGINE RUNTIME) ===\n");
    while (fgets(line, sizeof(line), file)) {
        printf("%s", line);
    }
    fclose(file);
}

void append_student(const char *nim, const char *nama, const char *jurusan, const char *status) {
    FILE *file = fopen(DB_FILE, "a");
    if (!file) {
        printf("Error: Gagal membuka berkas basis data untuk penulisan.\n");
        return;
    }
    fprintf(file, "%s,%s,%s,%s\n", nim, nama, jurusan, status);
    fclose(file);
    printf("Sukses: Mahasiswa NIM %s berhasil dicatat oleh sistem legacy.\n", nim);
}

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "add") == 0 && argc == 6) {
        append_student(argv[2], argv[3], argv[4], argv[5]);
    } else {
        list_students();
    }
    return 0;
}