# Spesifikasi HTML Saat Ini — Vault Knowledge Graph

File sumber generator: `vault_graph/export.py`

File hasil build: `vault-out/graph.html`

## Tujuan

Halaman HTML tunggal untuk menampilkan graph knowledge Vault menggunakan D3.js.

## Dependensi

- D3.js v7 dari `https://d3js.org/d3.v7.min.js`
- Tidak memakai framework frontend.
- Data graph disisipkan langsung ke HTML sebagai JavaScript.
- Bisa dibuka langsung dari filesystem melalui `file://`.

## Struktur Halaman

```text
<body>
├── #search
│   └── #search-input
├── #panel
│   ├── legend Wiki
│   ├── legend Session
│   ├── legend Concept
│   ├── legend Discord
│   ├── legend Minecraft
│   ├── legend Trae
│   ├── legend Other
│   └── #stats
├── #tooltip
├── #query-bar
│   ├── #query-input
│   └── Query button
└── #graph (SVG)
```

## Data yang Disisipkan

```js
const data = {
  nodes: [
    {
      id: "path/relative/ke/file.md",
      label: "Nama node",
      type: "session | concept | wiki | discord | minecraft | linux | trae-* | other",
      size: 5,
      community: 1
    }
  ],
  edges: [
    {
      source: "node-a",
      target: "node-b",
      relation: "wiki-link atau heading mention",
      confidence: "EXTRACTED | INFERRED"
    }
  ]
};
```

## Fitur Saat Ini

### Graph

- Force-directed graph D3.
- Node dapat di-drag.
- Canvas berupa SVG fullscreen.
- Zoom dan pan tersedia.
- Collision force mencegah node bertumpuk terlalu parah.
- Warna node berdasarkan `type`.
- Ukuran node berdasarkan `size`.
- Label node ditampilkan maksimal 28 karakter.

### Edge

- Edge `EXTRACTED` memakai garis solid.
- Edge `INFERRED` memakai garis putus-putus.
- Ketebalan edge extracted: `1.2`.
- Ketebalan edge inferred: `0.8`.

### Search

Input: `#search-input`

Pencarian berjalan saat mengetik dan mencocokkan:

- `node.label`
- `node.id`

Node yang cocok:

- Berubah menjadi putih.
- Membesar sekitar 2,2 kali.
- Minimum ukuran highlight: 14.

### Tooltip

Saat pointer masuk ke node, tooltip menampilkan:

- Label node.
- Tipe node.
- Nomor community jika tersedia.
- ID node maksimal 70 karakter.
- Jumlah koneksi.

Tooltip menggunakan `esc()` sebelum menampilkan label ke HTML.

### Query Bar

Format yang dikenali:

```text
path A to B
explain nama-node
community 3
kata pencarian biasa
```

Perilaku:

- `path A to B` mencari jalur terpendek menggunakan BFS sederhana.
- `explain nama-node` menampilkan detail node dan koneksinya.
- `community N` menyorot community tertentu.
- Teks biasa diteruskan ke fungsi search.

### Statistik

Panel menampilkan:

```text
<N> nodes · <M> edges
```

## Warna Saat Ini

| Type | Warna |
|---|---|
| wiki | `#4ecdc4` |
| session | `#ff6b6b` |
| concept | `#ffe66d` |
| discord | `#a29bfe` |
| minecraft | `#fd79a8` |
| linux | `#00b894` |
| trae-project | `#e17055` |
| trae-session | `#fab1a0` |
| trae-profile | `#d63031` |
| other | `#55efc4` |
| background | `#1a1a2e` |
| panel/border | `#3a3a5a` |

## CSS Saat Ini

- Dark theme.
- Font: `Segoe UI`, system-ui, sans-serif.
- Panel fixed di kanan atas.
- Search fixed di kiri atas.
- Query bar fixed di bawah tengah.
- Tooltip fixed dan pointer-events disabled.
- SVG mengisi viewport.
- Tidak ada layout mobile khusus.
- Tidak ada sidebar detail permanen.
- Tidak ada filter type/community.
- Tidak ada minimap.
- Tidak ada persistensi posisi node.
- Tidak ada loading/error state yang terpisah.

## Output Lain dalam Folder yang Sama

```text
vault-out/
├── graph.html       # visualisasi D3 saat ini
├── graph.json       # export JSON kompatibilitas
├── graph.db         # snapshot SQLite baru untuk query system
├── graph.svg        # visualisasi statis
├── mermaid.html     # visualisasi Mermaid
├── GRAPH_REPORT.md  # laporan statistik dan analisis
└── foam-vault/      # export Markdown dengan wiki-links
```

## Batasan untuk Redesign

- Jangan mengubah kontrak `data.nodes` dan `data.edges` tanpa memperbarui generator.
- `source` dan `target` edge harus tetap mengarah ke `node.id`.
- Label bisa berisi karakter Unicode.
- HTML sebaiknya tidak menganggap semua node memiliki `size`, `community`, atau `type`.
- Jangan menyimpan perubahan desain hanya di `vault-out/graph.html`; file itu akan ditimpa saat `vault-graph build`.
- Tempat perubahan utama tetap `vault_graph/export.py`.

## Arah Redesign yang Bisa Dipertimbangkan Nanti

- Sidebar detail node.
- Filter tipe, confidence, dan community.
- Tombol reset zoom dan fit graph.
- Mode fokus: tampilkan node terpilih beserta tetangganya.
- Search result list selain highlight node.
- Loading state dan pesan graph kosong.
- Responsive layout.
- Akses keyboard dan label ARIA.
- Export screenshot atau selected subgraph.
