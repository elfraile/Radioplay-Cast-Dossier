"""Assembles the unified Auris Szinkronstúdió Dossier with tabs:
1. Általános Színésztár (46 actors)
2. Rejtő Karakterarchívum (Tier 1 főszereplők + Tier 2 mellékszereplők)
Redesigned with rich illustrated character cards, large portraits, authentic Hungarian narrative lore,
collapsible appearance, actions, and psychology sections.
"""
import json
import re
import subprocess
from pathlib import Path

DOSSIER_DIR = Path(r"W:\AI\Projects\Auris-Cast-Dossier")
MASTER_DOSSIER_JSON = Path(r"W:\AI\Projects\Audiobook\Radioplay\docs\Rejto Cast Images\rejto_characters_complete_dossier.json")
TIER2_JSON = Path(r"W:\AI\Projects\Audiobook\Radioplay\docs\Rejto Cast Images\rejto_tier2_characters_clean.json")
INDEX_PATH = DOSSIER_DIR / "index.html"

# Get clean original HTML from git to avoid nested duplication
original_html = subprocess.check_output(
    ["git", "-C", str(DOSSIER_DIR), "show", "HEAD:index.html"],
    text=True, encoding="utf-8"
)

grid_start = original_html.find('<div class="actor-grid" id="actorGrid">')
if grid_start == -1:
    raise RuntimeError("actorGrid not found in original index.html")

container_close = original_html.find('</section>', grid_start)
if container_close == -1:
    raise RuntimeError("Closing </section> for actorGrid not found")

actor_cards_block = original_html[grid_start:container_close].strip()
# Ensure actor_cards_block properly closes
if not actor_cards_block.endswith('</div>'):
    actor_cards_block += '\n    </div>'

# Helper functions for Hungarian gender and age formatting
def format_gender_hu(raw_gender):
    if not raw_gender:
        return ""
    g = raw_gender.rstrip('.').strip().lower()
    if "férfi" in g or "male" in g:
        return "Férfi"
    elif "nő" in g or "female" in g:
        return "Nő"
    return raw_gender.rstrip('.').strip().capitalize()

def format_age_hu(raw_age):
    if not raw_age:
        return ""
    a = raw_age.rstrip('.').strip()
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*(?:years?\s*old)?', a, re.IGNORECASE)
    if m:
        return f"{m.group(1)}–{m.group(2)} év"
    return a

# Read Tier 1 characters from complete master dossier
chars_t1 = json.loads(MASTER_DOSSIER_JSON.read_text(encoding="utf-8"))

# Read Tier 2 characters if available
chars_t2 = {}
if TIER2_JSON.exists():
    try:
        raw_t2 = json.loads(TIER2_JSON.read_text(encoding="utf-8"))
        for k, v in raw_t2.items():
            chars_t2[k] = v
    except Exception as e:
        print(f"Tier 2 JSON not completely ready: {e}")

all_rejto_chars = {}
for k, v in chars_t1.items():
    v["tier_level"] = 1
    all_rejto_chars[k] = v

for k, v in chars_t2.items():
    # Only include Tier 2 character if their image exists OR passes stats threshold
    webp_path = DOSSIER_DIR / "rejto" / f"{k}.webp"
    stats = v.get("stats", {})
    lines = stats.get("lines_count", 0)
    words = stats.get("words_count", 0)
    
    # If image already generated OR qualifying stats:
    if webp_path.exists() or (stats and (lines >= 3 or words >= 25)):
        v["tier_level"] = 2
        all_rejto_chars[k] = v

rejto_cards_html = []
t1_count = sum(1 for v in all_rejto_chars.values() if v.get("tier_level") == 1)
t2_count = sum(1 for v in all_rejto_chars.values() if v.get("tier_level") == 2)

for name, d in all_rejto_chars.items():
    vis = d.get("visual_identity", {})
    psych = d.get("psychological_core", {})
    art = d.get("art_direction", {})
    book = d.get("book", "")
    tier_level = d.get("tier_level", 1)
    narrative = d.get("narrative_lore", {})
    ki_o = narrative.get("ki_o_valojaban", "")
    mit_csinalt = narrative.get("mit_csinalt_a_regenyben", [])

    webp_name = f"{name}.webp"
    has_webp = (DOSSIER_DIR / "rejto" / webp_name).exists()
    img_src = f"rejto/{webp_name}" if has_webp else ""

    audio_candidates = [f"{name}.wav", f"{name}.mp3"]
    if name == "A Főorvos Úr":
        audio_candidates.extend(["Főorvos Úr.wav", "Főorvos úr.wav"])
    elif name == "Kegyelmes úr":
        audio_candidates.extend(["Kegyelmes Úr.wav"])
    elif "Piszkos Fred" in name:
        audio_candidates.extend(["Piszkos Fred.wav"])

    audio_src = ""
    for cand in audio_candidates:
        if (DOSSIER_DIR / "rejto" / cand).exists():
            audio_src = f"rejto/{cand}"
            break

    gender_hu = format_gender_hu(vis.get("gender", ""))
    age_hu = format_age_hu(vis.get("age_bracket", ""))
    age_gender_str = f"{gender_hu} • {age_hu}" if (gender_hu and age_hu) else (gender_hu or age_hu)

    social = psych.get("social_role", "")
    contradiction = psych.get("signature_contradiction", "")
    constitution = vis.get("physical_constitution", "")
    somatic = vis.get("somatic_markers", "")
    attire = vis.get("attire_and_accessories", "")
    motivations = psych.get("motivations", "")
    temperament = psych.get("dominant_temperament", "")

    book_cat = "kapitany" if "a kapitány" in book.lower() and "közbelép" not in book.lower() else ("kozbelep" if "közbelép" in book.lower() and "a kapitány" not in book.lower() else "mindketto")
    has_audio_tag = "has-audio" if audio_src else "no-audio"
    is_master_tag = "is-master" if art.get("is_reference_master") else "normal"
    tier_tag = f"tier{tier_level}"

    stats = d.get("stats", {})

    # Bio block (Ki ő valójában - no header as requested)
    bio_html = f"""
      <div class="rejto-bio-block">
        <p class="rejto-bio-text">{ki_o}</p>
      </div>""" if ki_o else ""

    # Audio player block
    audio_html = f"""
      <div class="rejto-audio-block">
        <div class="rejto-audio-label">🎙️ Szinkronhang & akusztikai profil</div>
        <audio controls preload="none">
          <source src="{audio_src}" type="audio/wav">
        </audio>
      </div>""" if audio_src else ""

    # Accordion 1: Megjelenés és külső jegyek (Testalkat, vonások, öltözet, ellentmondás - NO Karikatúra)
    appearance_rows = []
    if constitution:
        appearance_rows.append(f'<div class="meta-row"><div class="meta-label">Testalkat</div><div class="meta-val meta-val-highlight">{constitution}</div></div>')
    if somatic:
        appearance_rows.append(f'<div class="meta-row"><div class="meta-label">Vonások & Arc</div><div class="meta-val">{somatic}</div></div>')
    if attire:
        appearance_rows.append(f'<div class="meta-row"><div class="meta-label">Öltözet & Kiegészítők</div><div class="meta-val">{attire}</div></div>')
    if contradiction:
        appearance_rows.append(f'<div class="meta-row"><div class="meta-label">Fő ellentmondás</div><div class="meta-val meta-val-contra">{contradiction}</div></div>')

    appearance_html = f"""
      <details class="rejto-accordion">
        <summary class="rejto-acc-summary">
          <span class="acc-title">👤 Megjelenés és külső jegyek</span>
          <span class="acc-chevron">▾</span>
        </summary>
        <div class="rejto-acc-body">
          {''.join(appearance_rows)}
        </div>
      </details>""" if appearance_rows else ""

    # Accordion 2: Mit csinált a regényben?
    actions_items = "".join([f"<li>{item}</li>" for item in mit_csinalt])
    actions_html = f"""
      <details class="rejto-accordion">
        <summary class="rejto-acc-summary">
          <span class="acc-title">📜 Mit csinált a regényben?</span>
          <span class="acc-chevron">▾</span>
        </summary>
        <div class="rejto-acc-body">
          <ul class="rejto-actions-list">
            {actions_items}
          </ul>
        </div>
      </details>""" if mit_csinalt else ""

    # Accordion 3: Jellem és pszicho
    psycho_rows = []
    if temperament:
        psycho_rows.append(f'<div class="meta-row"><div class="meta-label">Temperamentum</div><div class="meta-val">{temperament}</div></div>')
    if motivations:
        psycho_rows.append(f'<div class="meta-row"><div class="meta-label">Belső motivációk</div><div class="meta-val">{motivations}</div></div>')

    psycho_html = f"""
      <details class="rejto-accordion">
        <summary class="rejto-acc-summary">
          <span class="acc-title">🧠 Jellem és pszichológiai profil</span>
          <span class="acc-chevron">▾</span>
        </summary>
        <div class="rejto-acc-body">
          {''.join(psycho_rows)}
        </div>
      </details>""" if psycho_rows else ""

    # Separated technical footer tags
    tech_tags = []
    if social:
        tech_tags.append(f'<span class="tech-tag" title="Szereptípus">🎭 {social}</span>')
    if stats:
        tech_tags.append(f'<span class="tech-tag" title="Szereplési statisztika">📊 {stats.get("lines_count", 0)} sor • {stats.get("words_count", 0)} szó</span>')
    if art.get("is_reference_master"):
        tech_tags.append('<span class="tech-tag tech-master" title="Mester rajzstílus referencia">⭐ Stílus Etalon</span>')
    if audio_src:
        tech_tags.append('<span class="tech-tag tech-audio" title="Szinkronhang készleten">🎙️ Mesterhang</span>')

    tech_footer_html = f"""
      <div class="rejto-tech-footer">
        <div class="tech-tags-list">
          {''.join(tech_tags)}
        </div>
      </div>""" if tech_tags else ""

    card = f"""
    <div class="actor-card rejto-card" data-tier="{tier_tag}" data-book="{book_cat}" data-audio="{has_audio_tag}" data-master="{is_master_tag}" data-name="{name.lower()}" data-role="{social.lower()}" data-contra="{contradiction.lower()}" data-bio="{ki_o.lower()}">
      <div class="rejto-card-header">
        <div class="photo-frame rejto-photo-frame" data-img="{img_src}" data-name="{name}" data-contra="{contradiction.replace('"', '&quot;')}" onclick="handlePhotoFrameClick(this)" title="Kattints a nagyításhoz!">
          {f'<img src="{img_src}" alt="{name}" onerror="this.parentElement.innerHTML = getPlaceholderHtml();">' if img_src else '<div class="photo-placeholder"><span>Portré generálásra vár</span></div>'}
          <span class="zoom-hint">🔍 Nagyítás</span>
        </div>
        
        <div class="rejto-header-details">
          <div class="actor-name rejto-char-name">{name}</div>
          <div class="badge-row rejto-badge-row">
            <span class="badge badge-tier{'1' if tier_level == 1 else '2'}">{'👑 Főszereplő' if tier_level == 1 else '👥 Mellékszereplő'}</span>
            <span class="badge badge-book">📖 {book}</span>
            {f'<span class="badge badge-meta">👤 {age_gender_str}</span>' if age_gender_str else ''}
          </div>
        </div>
      </div>
      
      {bio_html}
      {audio_html}
      {appearance_html}
      {actions_html}
      {psycho_html}
      {tech_footer_html}
    </div>"""
    rejto_cards_html.append(card)

joined_rejto_cards = "\n".join(rejto_cards_html)

# Extract styles from original_html
style_start = original_html.find('<style>')
style_end = original_html.find('</style>')
existing_css = original_html[style_start + 7:style_end]

additional_css = """
  /* Studio Navigation Tabs */
  .studio-tabs {
    display: flex;
    justify-content: center;
    gap: 1.25rem;
    margin: 1.5rem 0 2.5rem 0;
    flex-wrap: wrap;
  }
  .studio-tab-btn {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    color: var(--text-secondary);
    padding: 0.95rem 1.8rem;
    border-radius: 14px;
    font-size: 1.05rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.25s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
  }
  .studio-tab-btn:hover {
    border-color: var(--accent);
    color: #fff;
    transform: translateY(-2px);
  }
  .studio-tab-btn.active {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.22) 0%, rgba(19, 23, 34, 0.95) 100%);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.3);
  }
  .studio-tab-btn.rejto-tab.active {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.22) 0%, rgba(19, 23, 34, 0.95) 100%);
    border-color: var(--accent-gold);
    color: #fff;
    box-shadow: 0 0 25px rgba(245, 158, 11, 0.3);
  }
  .tab-icon { font-size: 1.35rem; }
  .tab-badge {
    background: rgba(255, 255, 255, 0.08);
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-weight: 700;
  }
  .studio-tab-btn.active .tab-badge {
    background: rgba(56, 189, 248, 0.25);
    color: #38bdf8;
  }
  .studio-tab-btn.rejto-tab.active .tab-badge {
    background: rgba(245, 158, 11, 0.25);
    color: #f59e0b;
  }

  .tab-view { display: none; }
  .tab-view.active { display: block; animation: fadeIn 0.3s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

  /* Rejtő specific badges and accents */
  .badge-tier1 { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
  .badge-tier2 { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }
  .badge-book { background: rgba(56, 189, 248, 0.12); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }
  .badge-meta { background: rgba(148, 163, 184, 0.12); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.25); font-size: 0.8rem; padding: 0.3rem 0.65rem; border-radius: 6px; font-weight: 600; }
  .badge-audio { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
  .badge-master { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); }

  /* Rejtő Grid & Modern Showcase Card Design */
  #rejtoGrid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
    gap: 1.85rem;
  }

  .rejto-card {
    background: linear-gradient(180deg, #161b26 0%, #0d111a 100%);
    border: 1px solid rgba(245, 158, 11, 0.22);
    border-radius: 18px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .rejto-card:hover {
    border-color: rgba(245, 158, 11, 0.65);
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 0 25px rgba(245, 158, 11, 0.18);
    transform: translateY(-3px);
  }

  .rejto-card-header {
    display: flex;
    gap: 1.35rem;
    padding: 1.35rem 1.35rem 0.8rem 1.35rem;
    align-items: flex-start;
  }
  .rejto-photo-frame {
    width: 175px;
    height: 235px;
    border-radius: 12px;
    flex-shrink: 0;
    overflow: hidden;
    position: relative;
    border: 2px solid rgba(245, 158, 11, 0.4);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55), 0 0 12px rgba(245, 158, 11, 0.1);
    cursor: zoom-in;
    background: #0b0e14;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  }
  .rejto-photo-frame:hover {
    transform: scale(1.025);
    border-color: #f59e0b;
    box-shadow: 0 8px 25px rgba(245, 158, 11, 0.35);
  }
  .rejto-photo-frame img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .rejto-header-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .rejto-char-name {
    font-size: 1.45rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.01em;
    line-height: 1.25;
    margin: 0;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }
  .rejto-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* Story Bio Block (Ki ő valójában - no header) */
  .rejto-bio-block {
    margin: 0.4rem 1.35rem 1rem 1.35rem;
    padding: 1rem 1.15rem;
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(30, 41, 59, 0.35) 100%);
    border-left: 3px solid #f59e0b;
    border-radius: 0 10px 10px 0;
  }
  .rejto-bio-text {
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.68;
    color: #e2e8f0;
    font-weight: 400;
  }

  /* Audio player panel */
  .rejto-audio-block {
    margin: 0 1.35rem 1rem 1.35rem;
    padding: 0.75rem 1rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
  }
  .rejto-audio-label {
    font-size: 0.8rem;
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.45rem;
  }
  .rejto-audio-block audio {
    width: 100%;
    height: 38px;
  }

  /* Collapsible Accordions */
  .rejto-accordion {
    margin: 0 1.35rem 0.65rem 1.35rem;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.45);
    overflow: hidden;
    transition: all 0.2s ease;
  }
  .rejto-accordion:hover {
    border-color: rgba(245, 158, 11, 0.3);
  }
  .rejto-accordion[open] {
    border-color: rgba(245, 158, 11, 0.45);
    background: rgba(15, 23, 42, 0.75);
  }
  .rejto-acc-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 700;
    color: #cbd5e1;
    user-select: none;
    list-style: none;
    transition: color 0.2s ease;
  }
  .rejto-acc-summary::-webkit-details-marker {
    display: none;
  }
  .rejto-accordion[open] .rejto-acc-summary {
    color: #fbbf24;
    border-bottom: 1px solid rgba(245, 158, 11, 0.2);
  }
  .rejto-acc-chevron {
    font-size: 0.85rem;
    transition: transform 0.25s ease;
    color: #94a3b8;
  }
  .rejto-accordion[open] .rejto-acc-chevron {
    transform: rotate(180deg);
    color: #fbbf24;
  }
  .rejto-acc-body {
    padding: 0.9rem 1.1rem;
    font-size: 0.9rem;
    line-height: 1.55;
    color: #cbd5e1;
  }
  .rejto-acc-body .meta-row {
    margin-bottom: 0.65rem;
  }
  .rejto-acc-body .meta-row:last-child {
    margin-bottom: 0;
  }
  .rejto-acc-body .meta-label {
    font-weight: 700;
    color: #94a3b8;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.15rem;
  }
  .rejto-acc-body .meta-val {
    color: #e2e8f0;
  }
  .rejto-acc-body .meta-val-highlight {
    color: #f59e0b;
    font-weight: 600;
  }
  .rejto-acc-body .meta-val-contra {
    color: #38bdf8;
    font-style: italic;
  }
  .rejto-actions-list {
    margin: 0;
    padding-left: 1.25rem;
  }
  .rejto-actions-list li {
    margin-bottom: 0.55rem;
    line-height: 1.5;
    color: #e2e8f0;
  }
  .rejto-actions-list li::marker {
    color: #f59e0b;
  }
  .rejto-actions-list li:last-child {
    margin-bottom: 0;
  }

  /* Technical Tags Footer */
  .rejto-tech-footer {
    margin-top: auto;
    padding: 0.85rem 1.35rem;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    background: rgba(10, 14, 22, 0.5);
  }
  .tech-tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    align-items: center;
  }
  .tech-tag {
    font-size: 0.76rem;
    font-weight: 600;
    padding: 0.22rem 0.55rem;
    border-radius: 5px;
    background: rgba(255, 255, 255, 0.05);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .tech-tag.tech-master {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border-color: rgba(168, 85, 247, 0.35);
  }
  .tech-tag.tech-audio {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.35);
  }

  @media (max-width: 540px) {
    #rejtoGrid {
      grid-template-columns: 1fr;
    }
    .rejto-card-header {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
    .rejto-badge-row {
      justify-content: center;
    }
  }

  /* Lightbox Navigation Buttons */
  .modal-nav-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: rgba(19, 23, 34, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
    font-size: 1.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
    transition: all 0.2s ease;
    z-index: 100000;
    user-select: none;
  }
  .modal-nav-btn:hover {
    background: rgba(56, 189, 248, 0.35);
    border-color: var(--accent);
    color: #fff;
    transform: translateY(-50%) scale(1.08);
  }
  .modal-nav-prev { left: -68px; }
  .modal-nav-next { right: -68px; }
  .modal-counter {
    margin-top: 0.4rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  @media (max-width: 860px) {
    .modal-nav-prev { left: 8px; }
    .modal-nav-next { right: 8px; }
  }
"""

js_block = """
<script>
  let currentCategory = 'all';
  let currentRejtoFilter = 'all';
  let currentActiveTab = 'actors';

  // Lightbox navigation state
  let galleryItems = [];
  let currentGalleryIndex = -1;

  function getPlaceholderHtml() {
    return '<div class="photo-placeholder"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span>Portré generálásra vár</span></div>';
  }

  // Main Tab Switching
  function switchMainTab(tab) {
    currentActiveTab = tab;
    document.querySelectorAll('.studio-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));

    if (tab === 'rejto') {
      document.getElementById('tabBtnRejto').classList.add('active');
      document.getElementById('viewRejto').classList.add('active');
      location.hash = 'rejto';
    } else {
      document.getElementById('tabBtnActors').classList.add('active');
      document.getElementById('viewActors').classList.add('active');
      location.hash = 'actors';
    }
    document.querySelectorAll('audio').forEach(a => a.pause());
  }

  // Check URL hash on load
  window.addEventListener('DOMContentLoaded', () => {
    if (location.hash === '#rejto') {
      switchMainTab('rejto');
    }
  });

  // Actor Filters
  function setFilter(cat, btn) {
    currentCategory = cat;
    document.querySelectorAll('#viewActors .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterCards();
  }

  function filterCards() {
    const q = document.getElementById('searchInput').value.toLowerCase().trim();
    const cards = document.querySelectorAll('#actorGrid .actor-card');
    cards.forEach(card => {
      const cat = card.getAttribute('data-category');
      const name = card.getAttribute('data-name');
      const desc = card.getAttribute('data-desc');
      const reg = card.getAttribute('data-reg') || '';
      const morph = card.getAttribute('data-morph') || '';

      const matchesCat = (currentCategory === 'all' || cat === currentCategory);
      const matchesSearch = (!q || name.includes(q) || desc.includes(q) || reg.includes(q) || morph.includes(q));

      if (matchesCat && matchesSearch) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  }

  // Rejto Filters
  function setRejtoFilter(filter, btn) {
    currentRejtoFilter = filter;
    document.querySelectorAll('#viewRejto .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterRejtoCards();
  }

  function filterRejtoCards() {
    const q = document.getElementById('rejtoSearchInput').value.toLowerCase().trim();
    const cards = document.querySelectorAll('#rejtoGrid .actor-card');
    cards.forEach(card => {
      const tier = card.getAttribute('data-tier');
      const book = card.getAttribute('data-book');
      const audio = card.getAttribute('data-audio');
      const master = card.getAttribute('data-master');
      const name = card.getAttribute('data-name');
      const role = card.getAttribute('data-role') || '';
      const contra = card.getAttribute('data-contra') || '';
      const bio = card.getAttribute('data-bio') || '';

      let matchesFilter = false;
      if (currentRejtoFilter === 'all') matchesFilter = true;
      else if (currentRejtoFilter === 'tier1') matchesFilter = (tier === 'tier1');
      else if (currentRejtoFilter === 'tier2') matchesFilter = (tier === 'tier2');
      else if (currentRejtoFilter === 'kapitany') matchesFilter = (book === 'kapitany' || book === 'mindketto');
      else if (currentRejtoFilter === 'kozbelep') matchesFilter = (book === 'kozbelep' || book === 'mindketto');
      else if (currentRejtoFilter === 'master') matchesFilter = (master === 'is-master');
      else if (currentRejtoFilter === 'audio') matchesFilter = (audio === 'has-audio');

      const matchesSearch = (!q || name.includes(q) || role.includes(q) || contra.includes(q) || bio.includes(q));

      if (matchesFilter && matchesSearch) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  }

  // Build active gallery list from currently visible cards in the active tab
  function buildActiveGallery() {
    const gridId = (currentActiveTab === 'rejto') ? '#rejtoGrid' : '#actorGrid';
    const visibleCards = document.querySelectorAll(gridId + ' .actor-card');
    const items = [];
    visibleCards.forEach(card => {
      if (card.style.display !== 'none') {
        const frame = card.querySelector('.photo-frame');
        if (frame) {
          const imgEl = frame.querySelector('img');
          const imgSrc = frame.getAttribute('data-img') || (imgEl ? imgEl.getAttribute('src') : '');
          const name = frame.getAttribute('data-name') || (card.querySelector('.actor-name') ? card.querySelector('.actor-name').textContent.trim() : '');
          const desc = frame.getAttribute('data-contra') || '';
          if (imgSrc) {
            items.push({ imgSrc, name, desc });
          }
        }
      }
    });
    return items;
  }

  function handlePhotoFrameClick(frame) {
    const imgSrc = frame.getAttribute('data-img');
    const name = frame.getAttribute('data-name');
    const desc = frame.getAttribute('data-contra');
    openModal(imgSrc, name, desc);
  }

  // Modal Lightbox Functions
  function openModal(imgSrc, name, desc) {
    if (!imgSrc) return;
    galleryItems = buildActiveGallery();
    currentGalleryIndex = galleryItems.findIndex(item => item.imgSrc === imgSrc);
    if (currentGalleryIndex === -1 && imgSrc) {
      galleryItems.push({ imgSrc, name: name || '', desc: desc || '' });
      currentGalleryIndex = galleryItems.length - 1;
    }
    renderModalItem();

    const modal = document.getElementById('imageModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function renderModalItem() {
    if (currentGalleryIndex < 0 || currentGalleryIndex >= galleryItems.length) return;
    const item = galleryItems[currentGalleryIndex];
    const img = document.getElementById('modalImg');
    const title = document.getElementById('modalTitle');
    const sub = document.getElementById('modalSub');

    img.src = item.imgSrc;
    title.textContent = item.name;
    sub.textContent = item.desc ? '„' + item.desc + '”' : '';

    const counter = document.getElementById('modalCounter');
    if (counter) {
      counter.textContent = (currentGalleryIndex + 1) + ' / ' + galleryItems.length;
    }
  }

  function prevModalImage(e) {
    if (e) e.stopPropagation();
    if (!galleryItems.length) return;
    currentGalleryIndex = (currentGalleryIndex - 1 + galleryItems.length) % galleryItems.length;
    renderModalItem();
  }

  function nextModalImage(e) {
    if (e) e.stopPropagation();
    if (!galleryItems.length) return;
    currentGalleryIndex = (currentGalleryIndex + 1) % galleryItems.length;
    renderModalItem();
  }

  function closeModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }

  function closeModalOnBackdrop(e) {
    if (e.target.id === 'imageModal') {
      closeModal();
    }
  }

  document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('imageModal');
    if (!modal.classList.contains('active')) return;

    if (e.key === 'Escape') {
      closeModal();
    } else if (e.key === 'ArrowLeft') {
      prevModalImage();
    } else if (e.key === 'ArrowRight') {
      nextModalImage();
    }
  });
</script>
"""

new_html = (
    '<!DOCTYPE html>\n<html lang="hu">\n<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '<title>Auris Szinkronstúdió — Casting & Karakter Archívum</title>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Cinzel:wght@600;700&display=swap" rel="stylesheet">\n'
    f'<style>\n{existing_css}\n{additional_css}\n</style>\n</head>\n<body>\n'
    '<div class="container">\n'
    '  <header>\n'
    '    <div class="title-tag">Auris Audio Engine — Voice Cast & Character Archive</div>\n'
    '    <h1>Szinkronstúdió</h1>\n'
    '    <p class="subtitle">Professzionális színész- és karakterportfólió, akusztikai hangprofilok és mesterséges intelligencia által alkotott arcmások.</p>\n'
    '    <nav class="studio-tabs">\n'
    '      <button class="studio-tab-btn active" id="tabBtnActors" onclick="switchMainTab(\'actors\')">\n'
    '        <span class="tab-icon">🎭</span>\n'
    '        <span class="tab-label">Általános Színésztár</span>\n'
    '        <span class="tab-badge">46 Színész</span>\n'
    '      </button>\n'
    '      <button class="studio-tab-btn rejto-tab" id="tabBtnRejto" onclick="switchMainTab(\'rejto\')">\n'
    '        <span class="tab-icon">⚓</span>\n'
    '        <span class="tab-label">Rejtő Karakterarchívum</span>\n'
    f'        <span class="tab-badge">{len(all_rejto_chars)} Hős</span>\n'
    '      </button>\n'
    '    </nav>\n'
    '  </header>\n\n'
    '  <!-- ==================== TAB 1: ÁLTALÁNOS SZÍNÉSZTÁR ==================== -->\n'
    '  <section id="viewActors" class="tab-view active">\n'
    '    <div class="stats-bar">\n'
    '      <div class="stat-pill">👥 Összes színész: <strong>46 fő</strong></div>\n'
    '      <div class="stat-pill">⚖️ Nemek: <strong>24 Férfi / 22 Nő</strong></div>\n'
    '      <div class="stat-pill">🎙️ Akusztikai morfológia: <strong>46 alkat leképzés</strong></div>\n'
    '      <div class="stat-pill">⚡ Átlagos tempó: <strong>~147 WPM</strong></div>\n'
    '      <div class="stat-pill">🎨 Portré formátum: <strong>3:4 WebP (672×896)</strong></div>\n'
    '      <div class="stat-pill">🧠 Képtervező: <strong>Gemma 4 12B IT</strong></div>\n'
    '    </div>\n'
    '    <div class="controls-bar" style="margin-top: 2rem;">\n'
    '      <div class="search-box">\n'
    '        <input type="text" id="searchInput" placeholder="Keresés névre, karakterre, regiszterre vagy hangszínre..." oninput="filterCards()">\n'
    '      </div>\n'
    '      <div class="filter-group">\n'
    '        <button class="filter-btn active" onclick="setFilter(\'all\', this)">Mind (46)</button>\n'
    '        <button class="filter-btn" onclick="setFilter(\'Gyerek / Tini\', this)">Gyerek / Tini</button>\n'
    '        <button class="filter-btn" onclick="setFilter(\'Fiatal (20-30)\', this)">Fiatal (20-30)</button>\n'
    '        <button class="filter-btn" onclick="setFilter(\'Felnőtt (30-45)\', this)">Felnőtt (30-45)</button>\n'
    '        <button class="filter-btn" onclick="setFilter(\'Érett (45-60)\', this)">Érett (45-60)</button>\n'
    '        <button class="filter-btn" onclick="setFilter(\'Idős (60-80+)\', this)">Idős (60-80+)</button>\n'
    '      </div>\n'
    '    </div>\n'
    f'    {actor_cards_block}\n'
    '  </section>\n\n'
    '  <!-- ==================== TAB 2: REJTŐ KARAKTERARCHÍVUM ==================== -->\n'
    '  <section id="viewRejto" class="tab-view">\n'
    '    <div class="stats-bar">\n'
    f'      <div class="stat-pill">⚓ Összes aktív: <strong>{len(all_rejto_chars)} hős ({t1_count} fő- / {t2_count} mellékszereplő)</strong></div>\n'
    '      <div class="stat-pill">📖 Forrásművek: <strong>3 regényadaptáció</strong></div>\n'
    '      <div class="stat-pill">🎨 Képi világ: <strong>Vintage kalandképregény (Korcsmáros-stílus)</strong></div>\n'
    f'      <div class="stat-pill">🎙️ Mesterhangok: <strong>14 színész profil</strong></div>\n'
    '      <div class="stat-pill">📐 Méretarány: <strong>3:4 WebP nagyformátum</strong></div>\n'
    '      <div class="stat-pill">🤖 Generáló motor: <strong>gpt-image-2.5-sunburst</strong></div>\n'
    '    </div>\n'
    '    <div class="controls-bar" style="margin-top: 2rem;">\n'
    '      <div class="search-box">\n'
    '        <input type="text" id="rejtoSearchInput" placeholder="Keresés névre, történetre, cselekményre, vonásokra vagy szerepre..." oninput="filterRejtoCards()">\n'
    '      </div>\n'
    '      <div class="filter-group">\n'
    f'        <button class="filter-btn active" onclick="setRejtoFilter(\'all\', this)">Mind ({len(all_rejto_chars)})</button>\n'
    f'        <button class="filter-btn" onclick="setRejtoFilter(\'tier1\', this)">👑 Főszereplők ({t1_count})</button>\n'
    f'        <button class="filter-btn" onclick="setRejtoFilter(\'tier2\', this)">👥 Mellékszereplők ({t2_count})</button>\n'
    '        <button class="filter-btn" onclick="setRejtoFilter(\'kapitany\', this)">Piszkos Fred, a kapitány</button>\n'
    '        <button class="filter-btn" onclick="setRejtoFilter(\'kozbelep\', this)">Piszkos Fred közbelép</button>\n'
    '        <button class="filter-btn" onclick="setRejtoFilter(\'master\', this)">⭐ Stílus Etalonok</button>\n'
    '        <button class="filter-btn" onclick="setRejtoFilter(\'audio\', this)">🎙️ Mesterhanggal</button>\n'
    '      </div>\n'
    '    </div>\n'
    '    <div class="actor-grid" id="rejtoGrid">\n'
    f'{joined_rejto_cards}\n'
    '    </div>\n'
    '  </section>\n'
    '</div>\n\n'
    '<!-- Modal Lightbox -->\n'
    '<div id="imageModal" class="modal-overlay" onclick="closeModalOnBackdrop(event)">\n'
    '  <div class="modal-box">\n'
    '    <button class="modal-close-btn" onclick="closeModal()" title="Bezárás">&times;</button>\n'
    '    <button class="modal-nav-btn modal-nav-prev" onclick="prevModalImage(event)" title="Előző kép (Bal nyíl)">&#10094;</button>\n'
    '    <button class="modal-nav-btn modal-nav-next" onclick="nextModalImage(event)" title="Következő kép (Jobb nyíl)">&#10095;</button>\n'
    '    <img id="modalImg" class="modal-img" src="" alt="">\n'
    '    <div class="modal-info">\n'
    '      <div id="modalTitle" class="modal-name"></div>\n'
    '      <div id="modalSub" class="modal-sub"></div>\n'
    '      <div id="modalCounter" class="modal-counter"></div>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>\n\n'
    f'{js_block}\n'
    '</body>\n</html>'
)

INDEX_PATH.write_text(new_html, encoding="utf-8")
print(f"Successfully assembled unified Studio Dossier into {INDEX_PATH}")
