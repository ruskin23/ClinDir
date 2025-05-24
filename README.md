# ClinDir

AI‑powered PDF Directory organiser ― a lightweight pipeline that classifies, renames, and neatly shelves your PDF collection using OpenAI’s GPT models.

> Give ClinDir a folder of random PDFs and get back an ordered library of `./textbook/`, `./paper/`, `./lecture_notes/`, `./article/`, and `./other/` sub‑directories, with each file bearing an informative, snake‑case name.

---

## ✨ Features

| Capability                   | Details                                                                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Automatic classification** | The first \~20 pages of every PDF are fed to GPT‑4 to decide the `docType` and generate a description.            |
| **Smart renaming**           | Filenames are rewritten to `YYYY_author_keyword.pdf` (where data is available).                                   |
| **Directory routing**        | Files are copied into a relative folder that matches their `docType`, e.g. `./paper/2024_smith_transformers.pdf`. |
| **Idempotent processing**    | PDFs are fingerprinted via SHA‑256; already‑seen hashes are skipped.                                              |
| **Batch execution**          | Process files in configurable batch sizes for reliable long‑running jobs.                                         |
| **Transparent tracking**     | All processed items are appended to a JSON log so you can resume or audit later.                                  |

---

## 🚀 Quick start

```bash
# 1. Install uv (if you don’t have it)
python -m pip install uv

# 2. Clone your fork of the repo
git clone https://github.com/<you>/ClinDir.git
cd ClinDir

# 3. Create a virtual environment & install deps
uv venv .venv              # creates .venv via uv
source .venv/bin/activate  # (use .venv\Scripts\activate on Windows)
uv pip install -r requirements.txt

# 4. Export your OpenAI key (required)
export OPEN_API_KEY="sk‑..."   # Windows: setx OPEN_API_KEY "sk‑..."

# 5. Run the pipeline
python main.py \
  --pdf-dir      ./input_pdfs \
  --output-dir   ./organized_docs \
  --tracking-file ./tracking/processed.json \
  --batch-size   10
```

### Expected outcome

```
organized_docs/
├── article/
├── lecture_notes/
├── other/
├── paper/
└── textbook/
```

Each renamed PDF sits in the appropriate folder, and `./tracking/processed.json` records every processed file hash, its original location, new path, and GPT‑generated summary.

---

## 🛠️ Command‑line options

| Flag              | Required | Default | Purpose                                                                 |
| ----------------- | -------- | ------- | ----------------------------------------------------------------------- |
| `--pdf-dir`       | ✅        | —       | Directory containing input PDFs to process                              |
| `--output-dir`    | ✅        | —       | Destination root where organised folders will be created                |
| `--tracking-file` | ✅        | —       | JSON file used to persist processing history                            |
| `--batch-size`    | ❌        | `5`     | Number of PDFs to send per GPT batch (helps with rate‑limit resilience) |

---

## 🏗️ How it works – module tour

| File                   | Role                                                                                                                                                                                                     |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`main.py`**          | Orchestrates the end‑to‑end run: enumerates PDFs, skips seen hashes, batches work, calls the renamer, and copies files.                                                                                  |
| **`generators.py`**    | `NameChanger` class – asks GPT‑4 to produce `docType`, `description`, `newFileName`, and `pathToFile` given extracted text. The model name is hard‑coded as `gpt-4.1-2025-04-14`, but you can change it. |
| **`helpers.py`**       | Toolbox: file hashing, PDF text extraction (via `pdfminer`), directory‑tree utilities, batch helpers, and robust copy logic.                                                                             |
| **`models.py`**        | Pydantic models used across the code base (`OutputParsed`, `FileDescriptor`).                                                                                                                            |
| **`requirements.txt`** | Minimal dependency pin list; install with **uv** for fast binary‑cache resolution.                                                                                                                       |

---

## ⚙️ Configuration tips

| Setting               | Where                                           | Notes                                                                                |
| --------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| **OpenAI API key**    | Environment var `OPEN_API_KEY`                  | Mandatory. Obtain from [https://platform.openai.com/](https://platform.openai.com/). |
| **Model name**        | Environment var `MODEL_NAME`                    | Mandatory. Obtain from [https://platform.openai.com/](https://platform.openai.com/).                                         |
| **Batch size**        | CLI flag `--batch-size`                         | Tune based on your memory/throughput requirements.                                   |
| **Max pages per PDF** | `helpers.py → extract_text_from_pdf(max_pages)` | Default is 20 pages – increase for more context, but expect higher token costs.      |

---

## 💸 Cost considerations

Each PDF produces **one** ChatCompletion call. Billing scales with page count & model choice. To reduce spend:

* Lower `max_pages` in `helpers.extract_text_from_pdf`.
* Use a cheaper model and adjust the prompt accordingly.
* Batch runs during lower‑traffic hours to avoid rate‑limit retries.

---

## 🧪 Testing locally

Create a folder `sample_pdfs/` with a handful of small PDFs and run:

```bash
python main.py \
  --pdf-dir sample_pdfs \
  --output-dir sample_output \
  --tracking-file sample_tracking.json
```

Inspect `sample_output/` to confirm classification and naming are correct; check `sample_tracking.json` to verify metadata.

---

## 🤝 Contributing

1. Fork the project & create a feature branch.
2. Use **uv** in a fresh virtual environment (`uv venv .venv`).
3. Adhere to [PEP‑8](https://peps.python.org/pep-0008/) and format with `black`.
4. Ensure existing unit tests (coming soon!) pass with `pytest`.
5. Open a pull request – describe your changes and link to any relevant issues.

---

## 📜 License

Released under the MIT License. See `LICENSE` for full text.

---

## 🙏 Acknowledgements

* [OpenAI](https://openai.com/) for the amazing language models.
* [pdfminer‑six](https://github.com/pdfminer/pdfminer.six) for reliable PDF text extraction.
* The [uv](https://github.com/astral-sh/uv) team for blazing‑fast dependency installs.

Feel free to reach out by opening an issue if you hit a snag or have a feature request. Happy organising! ✨
