PFD workflow demonstration v2 / 75 seconds / 1080p / 24 fps

pfd-workflow-demo-v2-en.mp4: English synthesized narration.
pfd-workflow-demo-v2-zh.mp4: Chinese synthesized narration.
Both versions have the same visuals and burned-in short bilingual captions.
Full narration is available in captions-v2-*.vtt and transcript-v2.txt.

The sequence uses original PDF geometry, a recorded candidate graph and the
unchanged r010 scores of the historical 33-sheet A06 package. Animation reveals
saved artifacts; it is not a recording of new Agent execution. Equipment boxes
and path points in the Bench scene come from reader-panel114.json. Small numbers
are display indices, not equipment tags. The source input-to-CAD names are mapped
through the supplied identifier mapping; that mapping is not used for Bench reading.

Evidence: evidence.json and A06-demo-evidence-v2.zip. The builder checks original
XML, master DXF and candidate graph hashes against receipt p0119 before rendering.
Original input/drawing bytes and score values are unchanged.

Rebuild requirements: Python 3.12+, Pillow, PyMuPDF, FFmpeg and Windows fonts.
1. Extract the full historical HARD_A06 case including its 33 PDF drawing sheets.
2. Copy narration-v2.json to a private work directory as narration.json.
3. Generate WAVs with tools/make_demo_narration.ps1 (Windows SAPI voices).
4. Run tools/build_demo_v2.py --case-dir CASE --receipt RECEIPT_JSON
   --work WORK --ffmpeg FFMPEG_EXE. The receipt must point to the frozen graph.
The script uses Microsoft Zira Desktop and Huihui Desktop voice recordings,
normalizes audio levels, and exports a separate MP4 for each language.
No model API calls or new Agent execution are performed.

The old 90-second silent video and its captions are retained for version history.
python tools/build_demo.py --case-dir <original HARD_A06 folder> --receipt <original p0119.json> --ffmpeg <ffmpeg executable> --work <temporary frame directory>
The original receipt must still point to its frozen score vector and reading-freeze record. Windows fonts: Microsoft YaHei and Consolas.
