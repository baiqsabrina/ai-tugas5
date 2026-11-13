"""Sistem pakar diagnosis printer bermasalah (forward chaining).

Jalankan interaktif : python printer.py
Jalankan non-interaktif (untuk uji): python printer.py --ya "level tinta rendah" "hasil cetak pudar"
Keluaran otomatis disimpan berurutan: hasil/hasil1.txt, hasil/hasil2.txt, ...
"""
import argparse
import json
import os


# ======================================================================
# BAGIAN 1: FILE
# ======================================================================
def muat_kb(path):
    """Baca file aturan (JSON)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def nama_berikutnya(folder="hasil"):
    """Cari nama file hasil berikutnya: hasil1.txt, hasil2.txt, ..."""
    os.makedirs(folder, exist_ok=True)   # buat folder kalau belum ada

    terbesar = 0
    for nama in os.listdir(folder):
        if nama.startswith("hasil") and nama.endswith(".txt"):
            angka = nama[len("hasil"):-len(".txt")]   # "hasil3.txt" -> "3"
            if angka.isdigit():
                terbesar = max(terbesar, int(angka))

    return os.path.join(folder, "hasil" + str(terbesar + 1) + ".txt")


def simpan_hasil(keluaran, tujuan=None):
    """Tulis seluruh keluaran ke file txt, kembalikan nama file-nya."""
    if tujuan is None:
        tujuan = nama_berikutnya()
    with open(tujuan, "w", encoding="utf-8") as f:
        f.write("\n".join(keluaran) + "\n")
    return tujuan


# ======================================================================
# BAGIAN 2: MESIN FORWARD CHAINING
# ======================================================================
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


# ======================================================================
# BAGIAN 3: TAMPILAN
# ======================================================================
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


# ======================================================================
# BAGIAN 4: PROGRAM UTAMA
# ======================================================================
def baca_argumen():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="kb_printer.json")
    ap.add_argument("--ya", nargs="*", help="fakta yang dijawab ya (tanpa tanya)")
    ap.add_argument("--simpan", default=None, help="nama file txt (default: otomatis hasil/hasil1.txt, hasil2.txt, ...)")
    return ap.parse_args()


def main():
    args = baca_argumen()
    kb = muat_kb(args.kb)
    keluaran = []

    tulis(keluaran, kb["judul"])
    fakta = args.ya if args.ya is not None else tanya_fakta(kb, keluaran)
    memori, asal, log = forward_chaining(kb, fakta)
    tampilkan_hasil(kb, fakta, memori, asal, log, keluaran)

    tujuan = simpan_hasil(keluaran, args.simpan)
    print(f"\n(keluaran disimpan ke {tujuan})")


if __name__ == "__main__":
    main()
