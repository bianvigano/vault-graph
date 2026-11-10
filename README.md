# vault-graph

Knowledge graph dan pencarian knowledge lokal dari file Markdown Vault, dengan integrasi memory Trae dan MCP untuk AI.

Proyek pribadi [@bianvigano](https://github.com/bianvigano), lisensi MIT.

## Instalasi lokal (Linux)

Memerlukan Python 3.10+ dan [uv](https://docs.astral.sh/uv/). Dependensi dan model embedding membutuhkan koneksi internet saat pertama kali diunduh.

```bash
git clone https://github.com/bianvigano/vault-graph
cd vault-graph
uv sync
python3 install-cli.py
```

Pastikan `~/.local/bin` masuk ke `PATH`. Installer launcher membuat backup launcher lama jika backup belum tersedia. Launcher menggunakan environment proyek melalui `uv`, bukan Python sistem. Jangan pindahkan checkout setelah memasang launcher; jalankan installer ulang jika lokasi berubah.

Tanpa memasang launcher:

```bash
uv run python -m vault_graph.main --help
```

Installer lama `install.sh`/`install.bat` masih ada, tetapi jalur instalasi dan semantic retrieval terbaru yang diuji adalah Linux melalui `uv`. Dukungan Windows/macOS belum diverifikasi menyeluruh.

## Mulai memakai

```bash
# Build dengan lokasi Vault eksplisit dan model ringan
vault-graph build /path/ke/vault --model small

# Build berikutnya memakai lokasi dari konfigurasi
vault-graph build --model small

# Statistik dan pencarian node
vault-graph stats
vault-graph search Hermes
vault-graph search Hermes --interactive

# Pencarian isi Markdown
vault-graph retrieve "pengaturan server Minecraft"
vault-graph retrieve --semantic "bagaimana mengatur server Minecraft"

# Buka preview dari output yang sudah ada; tidak build ulang
vault-graph view

# Build ulang lalu buka preview
vault-graph view --build

# Alias lama, tetap didukung
vault-graph view --no-build

# Ctrl+C untuk berhenti setelah preview terbuka.
```

Build ulang diperlukan setelah sumber Markdown berubah. `watch` tersedia untuk rebuild otomatis, tetapi bisa mahal karena melibatkan indexing embedding.

## Pencarian dan halaman

`search` mencari label/path node graph, bukan isi Markdown.

```bash
vault-graph search Hermes --page 2 --page-size 15
vault-graph search Hermes --all
vault-graph search Hermes --interactive
```

Default: 15 hasil per halaman. Ukuran halaman: 1–100. Pada mode interaktif gunakan `n` (berikutnya), `p` (sebelumnya), nomor halaman, atau `q` (keluar).

Untuk isi dokumen, gunakan `retrieve` (SQLite FTS5/BM25) atau `retrieve --semantic` (embedding multilingual). Keduanya mengembalikan sumber dan citation, misalnya `[vault: minecraft/server/server-properties.md]`.

## Model embedding

Model yang didukung melalui Sentence Transformers:

| Pilihan | Model |
|---|---|
| `small` | `intfloat/multilingual-e5-small` |
| `base` | `intfloat/multilingual-e5-base` |
| `large` | `intfloat/multilingual-e5-large` |

```bash
vault-graph build --model small
vault-graph build --model base
vault-graph build --model large
vault-graph build                      # rekomendasi otomatis + benchmark sampel
```

Pemilihan otomatis saat ini memakai RAM tersedia, jumlah dokumen, dan CUDA:

- CUDA, RAM minimal 16 GB, maksimal 5.000 dokumen: kandidat `large`.
- RAM minimal 16 GB, maksimal 5.000 dokumen: kandidat `base`.
- Selain itu: kandidat `small`.

Sampel embedding digunakan untuk memperkirakan waktu indexing. Pada mode otomatis, estimasi lebih dari 600 detik menurunkan kandidat satu tingkat. Ini heuristik, bukan jaminan model terbaik: kapasitas VRAM belum dinilai dan model hasil penurunan belum dibenchmark ulang. Pemilihan manual tidak diturunkan otomatis.

Query selalu menggunakan model yang tersimpan di indeks. Mengganti model memerlukan build ulang seluruh embedding:

```bash
vault-graph retrieve --semantic --model small "pertanyaan"
```

`--model` pada query memvalidasi kecocokan indeks; tidak mengganti model atau melakukan rebuild. Query ditolak jika model berbeda.

Dokumen dipecah menggunakan tokenizer dengan target 440 token dan overlap 64 token. Prefix E5: `passage:` untuk dokumen dan `query:` untuk pertanyaan. Model di-cache selama satu proses hidup; command CLI baru tetap memuat model lagi. MCP dapat memakai proses yang bertahan hidup.

## Command lain

```bash
vault-graph god                        # node paling banyak koneksi
vault-graph explain "nama node"        # detail dan koneksi
vault-graph path "node A" "node B"      # jalur terpendek
vault-graph communities
vault-graph isolated
vault-graph query "pertanyaan"          # query graph, bukan jawaban LLM
vault-graph config show
vault-graph config path
vault-graph serve                      # server MCP stdio
vault-graph view --no-build --no-open --port 8765
```

## Konfigurasi

Lokasi Linux: `~/.config/vault-graph/config.json`.

```json
{
  "vault": "/home/user/vault",
  "out": "vault-out"
}
```

Path output relatif mengikuti lokasi Vault. Gunakan `vault-graph config path` untuk mengetahui lokasi konfigurasi mesin Anda. Lokasi Vault dapat ditetapkan lewat `build /path/ke/vault`.

## MCP untuk Hermes

Jalankan dari checkout atau daftarkan command dengan lokasi proyek absolut:

```bash
hermes mcp add vault-graph --command uv --args run --directory /path/ke/vault-graph python -m vault_graph.main serve
hermes mcp test vault-graph
```

Ikuti konfirmasi CLI Hermes. Muat ulang melalui `/reload-mcp` atau mulai sesi baru.

Tool yang tersedia:

- `graph_retrieve_context`: konteks BM25 dengan citation.
- `graph_semantic_context`: konteks semantic multilingual.
- `graph_search`, `graph_explain`, `graph_path`.
- `graph_god_nodes`, `graph_communities`, `graph_stats`.

Terdaftarnya MCP tidak menjamin AI selalu memanggilnya. Isi Vault harus diperlakukan sebagai data referensi tidak tepercaya, bukan instruksi. Informasi lama tetap perlu diverifikasi.

## Sumber dan output

Markdown tetap sumber pengetahuan. Graph juga dapat memasukkan data dari `~/.trae/memory/` jika tersedia. Indeks retrieval dokumen dibangun dari file Markdown yang dikumpulkan, bukan otomatis dari seluruh riwayat chat atau setiap node graph.

| File output | Fungsi |
|---|---|
| `graph.db` | SQLite untuk graph, indeks FTS5, chunk, dan embedding |
| `graph.json` | Export interoperabilitas/debug |
| `graph-data.js` | Export browser agar HTML bisa dibuka melalui `file://` |
| `graph.html` | Graph interaktif D3.js |
| `graph.svg` | Graph statis |
| `graph.mmd`, `mermaid.html` | Export Mermaid |
| `GRAPH_REPORT.md` | Laporan graph |

`vault-out/` adalah hasil build dan tidak disertakan dalam repository. Tampilan graph mungkin membutuhkan internet untuk library browser eksternal.

## Pemeriksaan

Dari checkout:

```bash
uv run python -m compileall -q vault_graph
uv run python check_retrieval.py
uv run python benchmark_retrieval.py
uvx --from pip-audit pip-audit --path .venv/lib/python3.12/site-packages --progress-spinner off
```

Sesuaikan path `site-packages` dengan versi Python environment. Benchmark saat ini memakai path Vault lokal pembuat proyek dan beberapa query Indonesia; sesuaikan `DB` dan sumber target sebelum menjalankannya di mesin lain.

Pengujian sebelumnya berhasil membangun 304 dokumen menjadi 806 chunk memakai model `small`, serta menemukan sumber Minecraft/Hermes yang diharapkan. Angka tersebut adalah snapshot, bukan batas kapasitas. Benchmark membedakan model indeks sebenarnya (`stored_model`) dari rekomendasi (`recommended_model`).

## Batasan yang diketahui

- `large` belum diverifikasi sampai indexing penuh selesai pada dataset lokal ini.
- Warning tokenizer untuk dokumen panjang masih terlihat pada build terakhir; jangan menganggap seluruh perilaku truncation sudah diverifikasi hanya dari keberhasilan build.
- Benchmark relevansi masih kecil, bukan evaluasi menyeluruh atau perbandingan tiga model.
- BM25 dan semantic masih terpisah; belum hybrid ranking.
- Beberapa chunk dari dokumen sama dapat muncul dalam hasil semantic.
- Audit dependency sebelumnya tidak menemukan kerentanan yang diketahui, tetapi bukan audit keamanan menyeluruh atau jaminan bebas bug. Package lokal tidak tercakup database kerentanan PyPI.
- Data knowledge lokal dapat berisi informasi sensitif. Batasi akses direktori Vault/database dan jangan mengekspos server preview atau MCP ke jaringan publik.

Lihat [docs/ai-memory.md](docs/ai-memory.md) untuk konteks retrieval AI. Jika ada perbedaan, perilaku kode dan hasil tes aktual menjadi acuan.

## Lisensi

MIT
