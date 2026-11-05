"""Assembles the unified Auris Szinkronstúdió Dossier with tabs:
1. Általános Színésztár (46 actors)
2. Rejtő Karakterarchívum (Tier 1 főszereplők + Tier 2 mellékszereplők)
"""
import json
import subprocess
from pathlib import Path

DOSSIER_DIR = Path(r"W:\AI\Projects\Auris-Cast-Dossier")
CONSOLIDATED_JSON = Path(r"W:\AI\Projects\Audiobook\Radioplay\docs\Rejto Cast Images\rejto_characters_consolidated.json")
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

container_close = original_html.find('\n</div>\n\n<!-- Modal Lightbox -->', grid_start)
if container_close == -1:
    container_close = original_html.find('<!-- Modal Lightbox -->', grid_start)

actor_cards_block = original_html[grid_start:container_close].strip()
# Enable lightbox navigation and clean click on general actor cards as well
actor_cards_block = actor_cards_block.replace(
    'class="photo-frame" onclick="openModal(',
    'class="photo-frame" onclick="openModal('
)

# Read Tier 1 characters
chars_t1 = json.loads(CONSOLIDATED_JSON.read_text(encoding="utf-8"))

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

    webp_name = f"{name}.webp"
    has_webp = (DOSSIER_DIR / "rejto" / webp_name).exists()
    img_src = f"rejto/{webp_name}" if has_webp else ""

    audio_candidates = [f"{name}.wav", f"{name}.mp3"]
    if name == "A Főorvos Úr":
        audio_candidates.append("Főorvos Úr.wav")
    elif name == "Kegyelmes úr":
        audio_candidates.append("Kegyelmes Úr.wav")

    audio_src = ""
    for cand in audio_candidates:
        if (DOSSIER_DIR / "rejto" / cand).exists():
            audio_src = f"rejto/{cand}"
            break

    age = vis.get("age_bracket", "")
    gender = vis.get("gender", "")
    social = psych.get("social_role", "")
    contradiction = psych.get("signature_contradiction", "")
    constitution = vis.get("physical_constitution", "")
    somatic = vis.get("somatic_markers", "")
    attire = vis.get("attire_and_accessories", "")
    motivations = psych.get("motivations", "")
    temperament = psych.get("dominant_temperament", "")
    caricature = art.get("caricature_focus", "")
    palette = art.get("palette", "")

    book_cat = "kapitany" if "a kapitány" in book.lower() and "közbelép" not in book.lower() else ("kozbelep" if "közbelép" in book.lower() and "a kapitány" not in book.lower() else "mindketto")
    has_audio_tag = "has-audio" if audio_src else "no-audio"
    is_master_tag = "is-master" if art.get("is_reference_master") else "normal"
    tier_tag = f"tier{tier_level}"

    stats = d.get("stats", {})
    stats_badge = f'<span class="badge badge-stats">📊 {stats.get("lines_count", 0)} sor • {stats.get("words_count", 0)} szó</span>' if stats else ""

    card = f"""
    <div class="actor-card rejto-card" data-tier="{tier_tag}" data-book="{book_cat}" data-audio="{has_audio_tag}" data-master="{is_master_tag}" data-name="{name.lower()}" data-role="{social.lower()}" data-contra="{contradiction.lower()}">
      <div class="card-top">
        <div class="photo-frame" data-img="{img_src}" data-name="{name}" data-contra="{contradiction.replace('"', '&quot;')}" onclick="handlePhotoFrameClick(this)" title="Kattints a nagyításhoz!">
          {f'<img src="{img_src}" alt="{name}" onerror="this.parentElement.innerHTML = getPlaceholderHtml();">' if img_src else '<div class="photo-placeholder"><span>Portré generálásra vár</span></div>'}
          <span class="zoom-hint">🔍 Nagyítás</span>
        </div>
        
        <div class="card-header-info">
          <div class="actor-name">{name}</div>
          <div class="badge-row">
            <span class="badge badge-tier{'1' if tier_level == 1 else '2'}">{'👑 Főszereplő' if tier_level == 1 else '👥 Mellékszereplő'}</span>
            <span class="badge badge-book">{book}</span>
            <span class="badge badge-cat">{gender} • {age}</span>
            <span class="badge badge-gender">{social}</span>
            {stats_badge}
            {f'<span class="badge badge-audio">🎙️ Mesterhang</span>' if audio_src else ''}
            {f'<span class="badge badge-master">⭐ Stílus Etalon</span>' if art.get("is_reference_master") else ''}
          </div>
          <div class="character-tagline">„{contradiction}”</div>
        </div>
      </div>
      
      {f'''
      <div class="audio-section">
        <audio controls preload="none">
          <source src="{audio_src}" type="audio/wav">
        </audio>
      </div>''' if audio_src else ''}

      <div class="card-body">
        <div class="meta-table">
          <div class="meta-label">Testalkat:</div>
          <div class="meta-val meta-val-highlight" style="color: #f59e0b;">{constitution}</div>

          <div class="meta-label">Vonások:</div>
          <div class="meta-val">{somatic}</div>

          <div class="meta-label">Öltözet:</div>
          <div class="meta-val">{attire}</div>

          <div class="meta-label">Ellentmondás:</div>
          <div class="meta-val meta-val-contra">{contradiction}</div>

          <div class="meta-label">Karikatúra:</div>
          <div class="meta-val">{caricature}</div>
        </div>

        <details>
          <summary>📖 Jellem és Pszichológiai Profil</summary>
          <div class="detail-box">
            <strong>Temperamentum:</strong> {temperament}<br>
            <strong>Motivációk:</strong> {motivations}<br>
            <strong>Szerep a műben:</strong> {social} ({book})
          </div>
        </details>

        <details>
          <summary>🎨 Vizuális Stílusirányelv (OpenAI Edit)</summary>
          <div class="detail-box prompt-text">
            <strong>Framing:</strong> {art.get("framing", "")}<br>
            <strong>Gesztus:</strong> {art.get("gesture", "")}<br>
            <strong>Mimika:</strong> {art.get("expression", "")}<br>
            <strong>Színpaletta:</strong> {palette}<br>
            <strong>Fókusz:</strong> {caricature}
          </div>
        </details>
      </div>
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
  .badge-audio { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
  .badge-master { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); }
  .badge-stats { background: rgba(255, 255, 255, 0.06); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.15); }
  .meta-val-contra { color: #f59e0b !important; font-weight: 600; line-height: 1.45; }
  .rejto-card:hover { border-color: #f59e0b; box-shadow: 0 12px 30px rgba(245, 158, 11, 0.2); }

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
      const role = card.getAttribute('data-role');
      const contra = card.getAttribute('data-contra');

      let matchesFilter = false;
      if (currentRejtoFilter === 'all') matchesFilter = true;
      else if (currentRejtoFilter === 'tier1') matchesFilter = (tier === 'tier1');
      else if (currentRejtoFilter === 'tier2') matchesFilter = (tier === 'tier2');
      else if (currentRejtoFilter === 'kapitany') matchesFilter = (book === 'kapitany' || book === 'mindketto');
      else if (currentRejtoFilter === 'kozbelep') matchesFilter = (book === 'kozbelep' || book === 'mindketto');
      else if (currentRejtoFilter === 'master') matchesFilter = (master === 'is-master');
      else if (currentRejtoFilter === 'audio') matchesFilter = (audio === 'has-audio');

      const matchesSearch = (!q || name.includes(q) || role.includes(q) || contra.includes(q));

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
          const desc = frame.getAttribute('data-contra') || (card.querySelector('.character-tagline') ? card.querySelector('.character-tagline').textContent.replace(/^[„"]+|[”"]+$/g, '').trim() : '');
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
    '      <div class="stat-pill">📖 Forrásművek: <strong>2 regényadaptáció</strong></div>\n'
    '      <div class="stat-pill">🎨 Rajzstílus: <strong>Vintage kalandképregény (1930s)</strong></div>\n'
    '      <div class="stat-pill">🎙️ Referencia hangminták: <strong>14 színész profil</strong></div>\n'
    '      <div class="stat-pill">📐 Méretarány: <strong>3:4 WebP (672×896 px)</strong></div>\n'
    '      <div class="stat-pill">🤖 Generáló motor: <strong>gpt-image-2.5-sunburst</strong></div>\n'
    '    </div>\n'
    '    <div class="controls-bar" style="margin-top: 2rem;">\n'
    '      <div class="search-box">\n'
    '        <input type="text" id="rejtoSearchInput" placeholder="Keresés névre, szerepre, ellentmondásra, öltözetre..." oninput="filterRejtoCards()">\n'
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
