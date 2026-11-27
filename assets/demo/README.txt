PFD demo / 90-second bilingual artifact walkthrough

Public evidence: evidence.json and A06-demo-evidence.zip.
The master DXF and input XML hashes are checked against receipt p0119 before rendering.
No model API calls or new Agent execution are performed by this video builder.
The source is the saved A06 recovery package, with 33 process sheets.
Captions are burned in English and Chinese; optional WebVTT tracks and transcript are also provided.

Rebuild: Python + Pillow + PyMuPDF + FFmpeg.
python tools/build_demo.py --case-dir <original HARD_A06 folder> --receipt <original p0119.json> --ffmpeg <ffmpeg executable> --work <temporary frame directory>
The original receipt must still point to its frozen score vector and reading-freeze record. Windows fonts: Microsoft YaHei and Consolas.
