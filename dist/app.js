'use strict';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const state = { demos: null, results: null, environment: 'halfcheetah', resultEnvironment: 'halfcheetah', metric: 'mean', heroPaused: reducedMotion.matches, speed: 1, autoPlayVisible: false };
const format = (value) => new Intl.NumberFormat('en-US', { maximumFractionDigits: Math.abs(value) < 100 ? 1 : 0 }).format(value);
const methodDescriptions = { fedguide: 'Personalized prior + DICE baseline', fedguide_a: 'Prior + DICE + policy averaging', fedguide_p: 'Personalized prior only' };
const methodClasses = { fedguide: 'blue-dot', fedguide_a: 'amber-dot', fedguide_p: 'green-dot' };

function makeTabs(target, environments, key, selected, onSelect, numbered = false) {
  target.replaceChildren(...environments.map((env, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.environment = env[key];
    button.setAttribute('aria-pressed', String(env[key] === selected));
    if (numbered) { const number = document.createElement('span'); number.className = 'tab-index'; number.textContent = String(index + 1).padStart(2, '0'); button.append(number); }
    button.append(env.name);
    button.addEventListener('click', () => onSelect(env[key]));
    return button;
  }));
}

function updateTabs(target, key) {
  target.querySelectorAll('button').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.environment === key)));
}

const heroObserver = new IntersectionObserver((entries) => {
  entries.forEach(({ target, isIntersecting }) => {
    target.dataset.visible = String(isIntersecting);
    if (isIntersecting && !state.heroPaused && !document.hidden) target.play().catch(() => {});
    else target.pause();
  });
}, { threshold: 0.15 });

function updateHeroMotion() {
  const button = $('#hero-motion');
  button.setAttribute('aria-pressed', String(state.heroPaused));
  button.textContent = state.heroPaused ? 'Play previews ▷' : 'Pause previews Ⅱ';
  $$('#hero-gallery video').forEach((video) => {
    if (!state.heroPaused && video.dataset.visible === 'true' && !document.hidden) video.play().catch(() => {});
    else video.pause();
  });
}

function renderHero() {
  const order = ['reacher', 'hopper', 'walker', 'halfcheetah', 'metaworld'];
  $('#hero-gallery').replaceChildren(...order.map((id) => {
    const env = state.demos.environments.find((item) => item.id === id);
    const clip = env.methods.find((method) => method.id === 'fedguide').videos['0'];
    const link = document.createElement('a');
    link.href = '#demonstrations';
    link.className = 'hero-tile';
    link.setAttribute('aria-label', `Explore ${env.name} policy demonstrations`);
    const video = document.createElement('video');
    Object.assign(video, { src: clip.src, poster: clip.poster, muted: true, loop: true, playsInline: true, preload: 'metadata' });
    video.setAttribute('aria-hidden', 'true');
    video.tabIndex = -1;
    video.style.objectPosition = `center ${id === 'halfcheetah' ? 65 : id === 'metaworld' ? 55 : 60}%`;
    const overlay = document.createElement('div');
    overlay.className = 'tile-overlay';
    const name = document.createElement('span'); name.textContent = env.name;
    const arrow = document.createElement('span'); arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
    overlay.append(name, arrow); link.append(video, overlay);
    link.addEventListener('click', () => selectEnvironment(id));
    heroObserver.observe(video);
    return link;
  }));
  updateHeroMotion();
}

function demoVideos() { return $$('#video-grid video'); }
function anyVideoPlaying() { return demoVideos().some((video) => !video.paused && !video.ended); }
function syncPlaybackUI() {
  const playing = state.autoPlayVisible || anyVideoPlaying();
  $('#play-all').innerHTML = playing ? '<span aria-hidden="true">Ⅱ</span> Pause all' : '<span aria-hidden="true">▶</span> Play as you scroll';
  $('#play-all').setAttribute('aria-label', playing ? 'Pause all demonstration videos' : 'Play visible client rows while scrolling');
  $('#play-all').setAttribute('aria-pressed', String(playing));
  $('#playback-status').textContent = state.autoPlayVisible ? 'Visible rows play automatically · muted' : 'All clients expanded · play a row or scroll to compare';
  $$('.client-row').forEach((row) => {
    const rowPlaying = [...row.querySelectorAll('video')].some((video) => !video.paused && !video.ended);
    const button = row.querySelector('.play-client');
    button.textContent = rowPlaying ? 'Ⅱ Pause row' : '▶ Play row';
    button.setAttribute('aria-label', `${rowPlaying ? 'Pause' : 'Play'} all methods for ${row.dataset.clientLabel}`);
    button.setAttribute('aria-pressed', String(rowPlaying));
  });
}

async function playVideos(videos) {
  const outcomes = await Promise.allSettled(videos.map((video) => video.play()));
  syncPlaybackUI();
  if (outcomes.some((outcome) => outcome.status === 'rejected')) $('#playback-status').textContent = 'Use the controls on a video if playback is unavailable.';
}

const demoObserver = new IntersectionObserver((entries) => {
  entries.forEach(({ target, isIntersecting }) => {
    target.dataset.visible = String(isIntersecting);
    if (!isIntersecting || document.hidden) target.pause();
    else if (state.autoPlayVisible) target.play().catch(() => {});
  });
}, { threshold: 0.2 });

function renderVideos(resume = false) {
  demoObserver.disconnect();
  demoVideos().forEach((video) => video.pause());
  const env = state.demos.environments.find((item) => item.id === state.environment);
  state.autoPlayVisible = resume;
  $('#video-grid').replaceChildren(...env.clients.map((client) => {
    const row = document.createElement('section');
    row.className = 'client-row';
    row.dataset.clientLabel = `${env.name}, ${client.label}`;
    const heading = document.createElement('header');
    heading.className = 'client-heading';
    const title = document.createElement('h4');
    title.id = `demo-client-${env.id}-${client.id}`;
    title.textContent = client.label;
    row.setAttribute('aria-labelledby', title.id);
    const rowButton = document.createElement('button');
    rowButton.type = 'button'; rowButton.className = 'play-client';
    rowButton.addEventListener('click', () => {
      const videos = [...row.querySelectorAll('video')];
      if (videos.some((video) => !video.paused && !video.ended)) {
        state.autoPlayVisible = false;
        videos.forEach((video) => video.pause());
      } else playVideos(videos);
      syncPlaybackUI();
    });
    heading.append(title, rowButton);
    const columns = document.createElement('div');
    columns.className = 'client-videos';
    columns.append(...env.methods.map((method) => {
      const clip = method.videos[String(client.id)];
      const card = document.createElement('article');
      card.className = `video-card${method.id === 'fedguide' ? ' featured' : ''}`;
      const header = document.createElement('header');
      const label = document.createElement('span');
      const dot = document.createElement('i'); dot.className = `legend-dot ${methodClasses[method.id]}`;
      label.append(dot, method.label);
      if (method.id === 'fedguide') { const badge = document.createElement('span'); badge.className = 'method-badge'; badge.textContent = 'FULL'; label.append(badge); }
      const seed = document.createElement('small'); seed.textContent = `seed ${clip.seed}`;
      header.append(label, seed);
      const video = document.createElement('video');
      Object.assign(video, { src: clip.src, poster: clip.poster, controls: true, muted: true, playsInline: true, preload: 'none', loop: true, playbackRate: state.speed });
      video.setAttribute('aria-label', `${method.label}, ${env.name}, client ${clip.client}, seed ${clip.seed}, round ${clip.round}`);
      video.addEventListener('play', syncPlaybackUI);
      video.addEventListener('pause', syncPlaybackUI);
      video.addEventListener('error', () => { $('#playback-status').textContent = 'A recording could not load. Please reload the page.'; });
      const footer = document.createElement('footer');
      footer.textContent = methodDescriptions[method.id];
      card.append(header, video, footer);
      return card;
    }));
    row.append(heading, columns);
    return row;
  }));
  demoVideos().forEach((video) => demoObserver.observe(video));
  syncPlaybackUI();
}

function selectEnvironment(id) {
  const resume = state.autoPlayVisible;
  state.environment = id;
  const env = state.demos.environments.find((item) => item.id === id);
  updateTabs($('#demo-tabs'), id);
  $('#demo-name').textContent = env.name;
  $('#demo-description').textContent = env.description;
  $('#client-count').textContent = `${env.clients.length} CLIENTS · ALL SHOWN`;
  renderVideos(resume);
}

function renderResult(id) {
  state.resultEnvironment = id;
  const env = state.results.environments.find((item) => item.key === id);
  const metric = env.metrics.fedguide;
  const baseline = env.bestExternalBaseline;
  const baselineMethod = state.results.methods.find((method) => method.key === baseline.method);
  updateTabs($('#result-tabs'), id);
  $('#result-curve').src = env.curve;
  $('#result-curve').alt = `${env.name}: client-average evaluation return across 100 federated rounds for seven methods. Mean and one standard error across five seeds.`;
  $('#insight-env').textContent = env.name.toUpperCase();
  $('#insight-mean').textContent = format(metric.mean);
  $('#insight-std').textContent = `± ${new Intl.NumberFormat('en-US', { maximumFractionDigits: metric.std < 1 ? 2 : 1 }).format(metric.std)}`;
  $('#baseline-number').textContent = format(baseline.mean);
  $('#baseline-caption').textContent = `${baselineMethod.name} · best external baseline`;
  const takeaway = id === 'reacher'
    ? 'FedGuide-P leads slightly (−12.2 vs. −12.3). Both outperform the external baselines.'
    : id === 'metaworld'
      ? 'Highest mean final return. Task-level heterogeneity remains challenging.'
      : `${baseline.ratio.toFixed(2)}× the final return of the strongest external baseline.`;
  $('#insight-takeaway').textContent = takeaway;
}

function renderTable() {
  const table = $('#results-table');
  const caption = document.createElement('caption'); caption.className = 'sr-only'; caption.textContent = `Main benchmark ${state.metric === 'mean' ? 'final' : 'worst-seed'} returns for seven methods`;
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  ['Environment', ...state.results.methods.map((method) => method.name)].forEach((name) => {
    const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = name; headRow.append(cell);
  });
  head.append(headRow);
  const body = document.createElement('tbody');
  state.results.environments.forEach((env) => {
    const row = document.createElement('tr');
    const name = document.createElement('th'); name.scope = 'row'; name.textContent = env.name; row.append(name);
    const best = Math.max(...state.results.methods.map((method) => env.metrics[method.key][state.metric]));
    state.results.methods.forEach((method) => {
      const metric = env.metrics[method.key];
      const value = metric[state.metric];
      const cell = document.createElement('td');
      if (method.key === 'fedguide') cell.classList.add('ours');
      if (value === best) cell.classList.add('best');
      cell.append(format(value));
      if (state.metric === 'mean') {
        const std = document.createElement('small');
        std.textContent = ` ± ${new Intl.NumberFormat('en-US', { maximumFractionDigits: metric.std < 10 ? 2 : 1 }).format(metric.std)}`;
        cell.append(std);
      }
      row.append(cell);
    });
    body.append(row);
  });
  table.replaceChildren(caption, head, body);
  $('#table-footnote').textContent = state.metric === 'mean'
    ? 'Final return: mean ± standard deviation of last-10-round means across five seeds. 8 clients per environment; 10 for MetaWorld10.'
    : 'Worst-seed return: the minimum last-10-round mean among five seeds. This measures variation across seeds, not across clients or individual rounds.';
}

$('#hero-motion').addEventListener('click', () => { state.heroPaused = !state.heroPaused; updateHeroMotion(); });
reducedMotion.addEventListener('change', (event) => { state.heroPaused = event.matches; updateHeroMotion(); });
document.addEventListener('visibilitychange', () => {
  updateHeroMotion();
  if (document.hidden) demoVideos().forEach((video) => video.pause());
  else if (state.autoPlayVisible) playVideos(demoVideos().filter((video) => video.dataset.visible === 'true'));
});
$('#play-all').addEventListener('click', () => {
  if (state.autoPlayVisible || anyVideoPlaying()) {
    state.autoPlayVisible = false;
    demoVideos().forEach((video) => video.pause());
  } else {
    state.autoPlayVisible = true;
    playVideos(demoVideos().filter((video) => video.dataset.visible === 'true'));
  }
  syncPlaybackUI();
});
$('#restart-all').addEventListener('click', () => { demoVideos().forEach((video) => { if (video.readyState > 0) video.currentTime = 0; }); syncPlaybackUI(); });
$('#playback-speed').addEventListener('change', (event) => { state.speed = Number(event.target.value); demoVideos().forEach((video) => { video.playbackRate = state.speed; }); });
$$('[data-metric]').forEach((button) => button.addEventListener('click', () => {
  state.metric = button.dataset.metric;
  $$('[data-metric]').forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
  renderTable();
}));
$('#copy-citation').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText($('#bibtex').textContent);
    $('#copy-citation span').textContent = 'Copied';
    $('#copy-status').textContent = 'BibTeX copied to clipboard.';
    setTimeout(() => { $('#copy-citation span').textContent = 'Copy BibTeX'; $('#copy-status').textContent = ''; }, 2500);
  } catch {
    const range = document.createRange(); range.selectNodeContents($('#bibtex'));
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    $('#copy-status').textContent = 'Citation selected. Press ⌘C (Mac) or Ctrl+C to copy.';
  }
});

const navigationObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) $$('.site-header nav a').forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
  });
}, { rootMargin: '-12% 0px -68% 0px' });
$$('main section[id]').forEach((section) => navigationObserver.observe(section));

async function readJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

Promise.allSettled([readJSON('demo-data.json'), readJSON('results-data.json')]).then(([demos, results]) => {
  if (demos.status === 'fulfilled') {
    state.demos = demos.value;
    renderHero();
    makeTabs($('#demo-tabs'), state.demos.environments, 'id', state.environment, selectEnvironment, true);
    selectEnvironment(state.environment);
  } else {
    $('#hero-gallery').innerHTML = '<p class="asset-error">Demonstrations could not load. Please serve this page over HTTP and reload.</p>';
    $('#playback-status').textContent = 'Demonstration data unavailable.';
    $('#play-all').disabled = true;
    $('#restart-all').disabled = true;
  }
  if (results.status === 'fulfilled') {
    state.results = results.value;
    makeTabs($('#result-tabs'), state.results.environments, 'key', state.resultEnvironment, renderResult);
    renderResult(state.resultEnvironment);
    renderTable();
  } else {
    $('#insight-takeaway').textContent = 'Interactive results could not load. See the paper for the full table.';
    $$('[data-metric]').forEach((button) => { button.disabled = true; });
  }
});
