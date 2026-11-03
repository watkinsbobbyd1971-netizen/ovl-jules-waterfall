1. **Explore the workspace** (done)
2. **Review task requirements:**
   - CATEGORY: CAT_20 (Weather, Atmospheric Optics, Fire, Fluid & Astronomic Phenomena)
   - ERA: 2020-2026
   - REGIONS: REG_01-05
   - REQUIRED DIMENSIONS: Length, width, and height MUST be explicit or strictly computed from explicit values on the cited page(s). Guessing is prohibited.
   - For irregular objects like meteorites, a single 'diameter' or 'mean diameter' measurement cannot be used to infer or extrapolate length, width, and height. All three dimensions must be explicitly and independently stated on the cited source; otherwise, the subject lacks required dimensions and must be skipped to avoid fabrication.
3. **Conduct exhaustive research:**
   - I have searched Wikipedia and the Meteoritical Bulletin extensively for meteorites and hailstones (e.g., El Ali meteorite, Wadsworth meteorite, Charlottetown meteorite, 2024 BX1, 2023 CX1, Markerville hailstone, Hondo hailstone).
   - In all these cases, we typically find a single diameter and/or mass, but *not* all three independent bounding box dimensions (length, width, height) explicitly stated.
   - For example, the Hondo hailstone has diameter, volume, and circumference. It does not have L, W, H.
   - The Markerville hailstone has diameter and weight. It lacks L, W, H.
   - 2024 BX1 has "diameter of 44 cm".
   - Wadsworth has "30 km" (strewn field length) and masses, but no individual dimensions for the meteorite fragments.
   - Charlottetown has diameter.
   - The 2026 Koblenz meteor mentions "few meters in diameter" and "centimeter-sized".
   - Since no subjects with explicitly stated independent L, W, H are found (and extrapolation from diameter is prohibited), I will create an empty output file `output/profile-ACC_06/batch_04_CAT20_2020S_R01-05_v3.jsonl`.
4. **Validation and Cleanup:**
   - Ensure the directory `output/profile-ACC_06/` exists via `mkdir -p output/profile-ACC_06/`.
   - Create an empty 0-byte file `touch output/profile-ACC_06/batch_04_CAT20_2020S_R01-05_v3.jsonl`.
   - Validate the empty file with `validate_jules_batch.py`.
   - Remove throwaway scripts with `rm` or `git clean -fdx -e pr_desc.txt`.
   - Stage the output file with `git add output/profile-ACC_06/batch_04_CAT20_2020S_R01-05_v3.jsonl`.
   - Commit the output file with `git commit -m "Submit batch_04 CAT20_2020S_R01-05_v3.jsonl"`.
5. **Complete pre-commit steps:**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
6. **Submit PR:**
   - Push the branch.
   - Generate PR description and create PR.
