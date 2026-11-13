"""Uji otomatis: python test_printer.py"""
import printer

kb = printer.muat_kb("kb_printer.json")


def akhir(fakta):
    memori, asal, _ = printer.forward_chaining(kb, fakta)
    return set(printer.kesimpulan_akhir(asal))


# --- syarat dari soal ---
def test_syarat_soal():
    aturan = kb["aturan"]
    assert len(aturan) >= 5, "minimal 5 aturan"
    assert len({a["maka"] for a in aturan}) >= 3, "minimal 3 kesimpulan"
    assert len(kb["sumber"]) >= 2, "minimal 2 sumber"
    assert all(a["sumber"] in kb["sumber"] for a in aturan), "tiap aturan menunjuk sumber"
    hasil = {a["maka"] for a in aturan}
    assert any(f in hasil for a in aturan for f in a["jika"]), "ada aturan berantai"
    assert all(a["mode"] in ("dan", "atau") for a in aturan)
    assert kb["batas"] and kb["judul"]


# --- kasus uji ---
def test_kasus_1():
    assert akhir(["pesan paper jam muncul", "error tetap setelah kertas dikeluarkan"]) == {"sisa kertas atau sensor jam masih aktif"}

def test_kasus_2():
    assert akhir(["hasil cetak pudar", "level tinta rendah"]) == {"tinta perlu diisi atau diganti"}

def test_kasus_3():
    assert akhir(["dokumen tertahan di antrean", "tetap macet setelah job dibatalkan"]) == {"print spooler perlu direstart"}

def test_kasus_negatif():
    assert akhir(["level tinta rendah"]) == set()
    assert akhir([]) == set()

def test_dua_kesimpulan():
    assert akhir(["hasil cetak bergaris atau ada celah", "hasil nozzle check ada celah", "level tinta rendah"]) == {
        "tinta perlu diisi atau diganti", "kepala cetak tersumbat"}

def test_mode_dan_butuh_semua():
    assert akhir(["pesan paper jam muncul"]) == {"kertas macet"}  # R2 butuh 2 syarat

def test_berhenti_tidak_loop():
    semua = printer.fakta_dasar(kb)
    memori, asal, log = printer.forward_chaining(kb, semua)
    assert len(log) <= len(kb["aturan"]) + 1


if __name__ == "__main__":
    gagal = 0
    for nama, fn in list(globals().items()):
        if nama.startswith("test_"):
            try:
                fn(); print("LULUS ", nama)
            except AssertionError as e:
                gagal += 1; print("GAGAL ", nama, e)
    print("\nSemua lulus" if not gagal else f"\n{gagal} gagal")
