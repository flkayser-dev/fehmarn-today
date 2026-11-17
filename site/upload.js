// PROTOTYP: Termin melden / Angebot eintragen, mit Foto-Upload (Vorschau, Prüfung). Es wird nichts gesendet.
(() => {
  const MAX_FILES = 4;
  const MAX_BYTES = 8 * 1024 * 1024;
  const TYPES = ['image/jpeg', 'image/png', 'image/webp'];

  // Umschalten zwischen den beiden Formularen
  const tabs = document.querySelectorAll('.sub-tabs button');
  tabs.forEach((b) => b.addEventListener('click', () => {
    tabs.forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    ['f-termin', 'f-angebot'].forEach((id) => { document.getElementById(id).hidden = id !== b.dataset.form; });
    document.querySelectorAll('.sub-text').forEach((p) => { p.hidden = p.dataset.for !== b.dataset.form; });
  }));

  document.querySelectorAll('[data-upload]').forEach((box) => {
    const input = box.querySelector('.upload-input');
    const drop = box.querySelector('.upload-drop');
    const list = box.querySelector('.upload-list');
    const err = box.querySelector('.upload-err');
    let files = [];

    function render() {
      list.innerHTML = '';
      files.forEach((f, i) => {
        const li = document.createElement('li');
        li.className = 'upload-item';
        const img = document.createElement('img');
        img.src = URL.createObjectURL(f);
        img.alt = `Vorschau ${i + 1}: ${f.name}`;
        img.onload = () => URL.revokeObjectURL(img.src);
        const rm = document.createElement('button');
        rm.type = 'button';
        rm.className = 'upload-rm';
        rm.textContent = 'Entfernen';
        rm.setAttribute('aria-label', `Foto ${f.name} entfernen`);
        rm.addEventListener('click', () => { files.splice(i, 1); err.textContent = ''; render(); });
        li.append(img, rm);
        list.append(li);
      });
      drop.querySelector('.upload-cta').textContent = files.length ? 'Weitere Fotos auswählen' : 'Fotos auswählen';
      box.classList.toggle('has-files', files.length > 0);
    }

    function add(incoming) {
      const problems = [];
      [...incoming].forEach((f) => {
        if (!TYPES.includes(f.type)) problems.push(`${f.name}: nur JPG, PNG oder WebP`);
        else if (f.size > MAX_BYTES) problems.push(`${f.name}: größer als 8 MB`);
        else if (files.length >= MAX_FILES) problems.push(`Höchstens ${MAX_FILES} Fotos`);
        else if (!files.some((x) => x.name === f.name && x.size === f.size)) files.push(f);
      });
      err.textContent = [...new Set(problems)].join('. ');
      render();
    }

    input.addEventListener('change', () => { add(input.files); input.value = ''; });
    ['dragenter', 'dragover'].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add('is-over'); }));
    ['dragleave', 'drop'].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove('is-over'); }));
    drop.addEventListener('drop', (e) => add(e.dataTransfer.files));
    box.getFiles = () => files;
  });

  // Absenden: prüfen, dann Prototyp-Hinweis (kein Versand)
  document.querySelectorAll('#melden form').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const note = form.querySelector('.form-note');
      const box = form.querySelector('[data-upload]');
      const n = box ? box.getFiles().length : 0;
      const rights = form.querySelector('input[name="rights"]');
      const missing = [...form.querySelectorAll('[required]')].filter((el) => el !== rights && !el.value.trim());
      if (missing.length) {
        note.textContent = 'Bitte die Pflichtfelder ausfüllen.';
        missing[0].focus();
        return;
      }
      if (n && !rights.checked) {
        note.textContent = 'Bitte bestätigen, dass Sie die Fotos zeigen dürfen.';
        rights.focus();
        return;
      }
      note.textContent = `Prototyp: Das Formular ist noch nicht angeschlossen, es wurde nichts gesendet${n ? ` (${n} ${n === 1 ? 'Foto' : 'Fotos'} geprüft)` : ''}.`;
    });
  });
})();
