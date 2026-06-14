# 🚀 How to Set Up Your GitHub Repository (Step by Step)

## Step 1 — Create GitHub Account & Repository

1. Go to **https://github.com** → Sign Up (or Log In)
2. Click the **"+"** icon (top right) → **New repository**
3. Fill in:
   - **Repository name**: `trackguard-ai`
   - **Description**: `Autonomous Railway Safety System - FAR AWAY 2026`
   - **Visibility**: ✅ Public (required for FAR AWAY)
   - ✅ Check "Add a README file"
4. Click **"Create repository"**

---

## Step 2 — Install Git on Your Computer

### Windows:
Download from https://git-scm.com/download/win → Install with defaults

### Linux/Mac:
```bash
sudo apt install git    # Ubuntu/Debian
brew install git        # Mac
```

Configure Git (do this once):
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## Step 3 — Clone & Add Your Files

```bash
# Clone your new repo
git clone https://github.com/[YOUR_USERNAME]/trackguard-ai.git
cd trackguard-ai

# Copy all project files into this folder
# (Copy app/, backend/, robot/, arduino/, pcb/, docs/, demo/ here)
```

---

## Step 4 — Add All Files & Push

```bash
# Add everything
git add .

# Commit with a message
git commit -m "Initial commit - TrackGuard AI FAR AWAY 2026"

# Push to GitHub
git push origin main
```

---

## Step 5 — Add Required Files for FAR AWAY

Make sure these exist in your repo:
- [ ] `README.md` — already created
- [ ] `docs/BOM.csv` — Bill of Materials ✅
- [ ] `pcb/` folder with KiCad files
- [ ] `demo/screenshots/` — at least 3 screenshots
- [ ] `demo/VIDEO_LINK.txt` — YouTube/Drive link to demo video

---

## Step 6 — Add Demo Video

1. Record a 2–5 minute demo video showing:
   - The citizen app opening on phone
   - Reporting a hazard with photo
   - Dashboard showing the report in real-time
   - Robot simulation OR physical robot on mock track
2. Upload to YouTube (unlisted is fine) or Google Drive
3. Paste the link in `demo/VIDEO_LINK.txt`
4. `git add . && git commit -m "Add demo video link" && git push`

---

## Step 7 — Final Push Before Deadline

```bash
git add .
git commit -m "Final submission - FAR AWAY 2026"
git push origin main
```

✅ **Submit the GitHub URL**: `https://github.com/[YOUR_USERNAME]/trackguard-ai`

---

## Useful Git Commands

```bash
git status              # See what changed
git add filename.py     # Add specific file
git add .               # Add all files
git commit -m "message" # Save snapshot
git push                # Upload to GitHub
git log --oneline       # See commit history
```
