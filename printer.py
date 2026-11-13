
import json

NAMA_KB = "kb_printer.json"

# BAGIAN 1: FILE
def muat_kb(path):
    """Baca file aturan (JSON) dan kembalikan sebagai dictionary."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_ada(nama):
    """True kalau file dengan nama itu sudah ada."""
    try:
        f = open(nama, encoding="utf-8")
        f.close()
        return True
    except FileNotFoundError:
        return False


def nama_berikutnya():
    """Cari nama file hasil yang belum dipakai: hasil1.txt, hasil2.txt, ..."""
    nomor = 1
    while file_ada("hasil/hasil" + str(nomor) + ".txt"):
        nomor += 1
    return "hasil/hasil" + str(nomor) + ".txt"


def simpan_hasil(keluaran):
    """Tulis seluruh keluaran ke file txt berurutan."""
    tujuan = nama_berikutnya()
    try:
        with open(tujuan, "w", encoding="utf-8") as f:
            f.write("\n".join(keluaran) + "\n")
        print(f"\n(keluaran disimpan ke {tujuan})")
    except FileNotFoundError:
        print("\n(folder 'hasil' belum ada, buat dulu foldernya lalu jalankan lagi)")


# BAGIAN 2: MESIN FORWARD CHAINING
def fakta_dasar(kb):
    """Fakta yang tidak pernah menjadi hasil aturan -> ditanyakan ke user."""
    semua_hasil = []
    for aturan in kb["aturan"]:
        semua_hasil.append(aturan["maka"])

    fakta = []
    for aturan in kb["aturan"]:
        for syarat in aturan["jika"]:
            if syarat not in semua_hasil and syarat not in fakta:
                fakta.append(syarat)
    return fakta


def terpenuhi(aturan, memori):
    """Cek apakah syarat aturan terpenuhi oleh isi memori."""
    jumlah_ada = 0
    for syarat in aturan["jika"]:
        if syarat in memori:
            jumlah_ada += 1

    if aturan["mode"] == "dan":
        return jumlah_ada == len(aturan["jika"])   # semua syarat harus ada
    return jumlah_ada >= 1                          # mode "atau": salah satu cukup


def forward_chaining(kb, fakta_awal):
    memori = set(fakta_awal)
    asal = {}    # hasil -> aturan yang menghasilkannya (bahan "alasan")
    log = []
    siklus = 0

    while True:
        siklus += 1

        # aturan yang syaratnya terpenuhi DAN hasilnya belum ada di memori
        cocok = []
        for aturan in kb["aturan"]:
            if aturan["maka"] not in memori and terpenuhi(aturan, memori):
                cocok.append(aturan)

        if len(cocok) == 0:
            log.append(f"Siklus {siklus}: tidak ada aturan baru, berhenti")
            break

        r = cocok[0]                 # ambil aturan pertama
        memori.add(r["maka"])        # tambahkan hasilnya ke memori
        asal[r["maka"]] = r          # catat asalnya
        log.append(f"Siklus {siklus}: {r['id']} -> {r['maka']}")

    return memori, asal, log


def kesimpulan_akhir(asal):
    """Kesimpulan akhir = hasil yang tidak dipakai sebagai syarat aturan lain."""
    dipakai = set()
    for aturan in asal.values():
        for syarat in aturan["jika"]:
            dipakai.add(syarat)

    akhir = []
    for hasil in asal:
        if hasil not in dipakai:
            akhir.append(hasil)
    return akhir



# BAGIAN 3: TAMPILAN
def tulis(keluaran, teks=""):
    """Cetak ke layar dan catat ke daftar keluaran (untuk disimpan ke txt)."""
    print(teks)
    keluaran.append(teks)


def tanya_fakta(kb, keluaran):
    """Tanyakan fakta dasar ke user, kembalikan daftar fakta yang dijawab ya."""
    tulis(keluaran, "Jawab y/t.")
    fakta = []
    nomor = 1
    for f in fakta_dasar(kb):
        tanya = f"{nomor}. {kb['pertanyaan'].get(f, f)} (y/t) > "
        jawab = input(tanya).strip().lower()
        keluaran.append(tanya + jawab)    # input() tidak lewat tulis(), catat manual
        if jawab == "y":
            fakta.append(f)
        nomor += 1
    return fakta


def cetak_alasan(hasil, asal, memori, keluaran, tingkat=1):
    """Tampilkan aturan yang menghasilkan 'hasil'. Memanggil dirinya sendiri
    untuk menelusuri hasil antara (misal R2 memakai hasil R1)."""
    r = asal[hasil]

    syarat_benar = []
    for f in r["jika"]:
        if f in memori:
            syarat_benar.append(f)

    tulis(keluaran, "  " * tingkat + f"{hasil}  <- {r['id']} ({', '.join(syarat_benar)}) [{r['sumber']}]")

    for f in syarat_benar:
        if f in asal:    # syarat ini ternyata hasil aturan lain -> telusuri
            cetak_alasan(f, asal, memori, keluaran, tingkat + 1)


def tampilkan_hasil(kb, fakta, memori, asal, log, keluaran):
    tulis(keluaran, "\nFakta awal: " + (", ".join(fakta) if fakta else "(tidak ada)"))
    tulis(keluaran)
    tulis(keluaran, "\n".join(log))

    akhir = kesimpulan_akhir(asal)
    tulis(keluaran)
    if len(akhir) == 0:
        tulis(keluaran, "Kesimpulan: tidak ada kesimpulan dari fakta yang diberikan")
    else:
        tulis(keluaran, "Kesimpulan: " + ", ".join(akhir))

        tulis(keluaran, "Saran:")
        for h in akhir:
            tulis(keluaran, f"  - {h}: {kb['saran'].get(h, '-')}")

        tulis(keluaran, "Alasan:")
        for h in akhir:
            cetak_alasan(h, asal, memori, keluaran)

        sumber_dipakai = []
        for aturan in asal.values():
            if aturan["sumber"] not in sumber_dipakai:
                sumber_dipakai.append(aturan["sumber"])
        tulis(keluaran, "Sumber:")
        for s in sorted(sumber_dipakai):
            tulis(keluaran, f"  {s}: {kb['sumber'][s]}")

    tulis(keluaran, "\nCatatan: " + kb["batas"])


# BAGIAN 4: PROGRAM UTAMA
def main():
    kb = muat_kb(NAMA_KB)
    keluaran = []

    tulis(keluaran, kb["judul"])
    fakta = tanya_fakta(kb, keluaran)
    memori, asal, log = forward_chaining(kb, fakta)
    tampilkan_hasil(kb, fakta, memori, asal, log, keluaran)
    simpan_hasil(keluaran)


if __name__ == "__main__":
    main()