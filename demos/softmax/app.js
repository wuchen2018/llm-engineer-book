import { softmax, filterProbabilities, sampleIndex } from './model.mjs';

const $ = id => document.getElementById(id);
const tokens = ['好', '差', '的', '了', '不'];
const original = [3.2, 0.8, 1.5, 0.3, -0.5];
const colors = ['#14523f', '#b56632', '#416b9b', '#8a5979', '#5c7369'];
const percentage = value => value > 0 && value < 0.001 ? '<0.1%' : `${(value * 100).toFixed(1)}%`;
const decimal = value => value !== 0 && (Math.abs(value) < 0.0001 || Math.abs(value) >= 1e8)
  ? value.toExponential(4)
  : new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 4 }).format(value);
let scores = [...original];
let temperature = 1;
let mode = 'all';
let topK = 3;
let topP = 0.9;
let counts = [0, 0, 0, 0, 0];
let probabilities = [];
let finalProbabilities = [];
let animation = null;
let lastDraw = null;

tokens.forEach((token, i) => {
  const row = document.createElement('div');
  row.className = 'probability-row';
  row.innerHTML = `<span class="word">${token}</span><div class="bar-track"><span class="probability-bar" id="bar-${i}"></span></div><strong id="probability-${i}"></strong><span class="score-label" id="score-label-${i}"></span>`;
  $('probability-rows').append(row);
  $(`bar-${i}`).style.background = colors[i];
});

function stopBatch() {
  if (animation !== null) cancelAnimationFrame(animation);
  animation = null;
  $('sample-many').textContent = '连续抽1000次';
}

function clearSamples(message = '点“按当前概率抽1次”，看看随机数落在哪一段。') {
  stopBatch(); counts = [0, 0, 0, 0, 0]; lastDraw = null;
  $('random-marker').hidden = true;
  $('chosen-word').textContent = '____';
  $('draw-description').textContent = message;
  renderSamples();
}

function renderSamples() {
  const total = counts.reduce((a, b) => a + b, 0);
  $('sample-caption').textContent = total ? `累计抽了${total.toLocaleString('zh-CN')}次。参数改变后，抽样次数会重新开始。` : '还没有抽样。先看理论概率，再抽几次比较。';
  $('sample-results').innerHTML = tokens.map((token, i) => `<tr${lastDraw?.index === i ? ' class="last-picked"' : ''}><th scope="row"><span class="swatch" style="background:${colors[i]}"></span>${token}${finalProbabilities[i] === 0 ? '<span class="excluded">已筛掉</span>' : ''}</th><td>${percentage(finalProbabilities[i])}</td><td>${counts[i].toLocaleString('zh-CN')}</td><td>${total ? percentage(counts[i] / total) : '—'}</td></tr>`).join('');
}

function renderDistribution() {
  probabilities = softmax(scores, temperature);
  finalProbabilities = filterProbabilities(probabilities, mode, mode === 'top-k' ? topK : topP);
  probabilities.forEach((probability, i) => {
    $(`bar-${i}`).style.width = `${probability * 100}%`;
    $(`probability-${i}`).textContent = percentage(probability);
    $(`score-label-${i}`).textContent = `原始分数 ${scores[i]}`;
  });
  $('probability-chart').setAttribute('aria-label', `温度${temperature}，${tokens.map((token, i) => `${token}的概率${percentage(probabilities[i])}`).join('，')}。`);
  const best = probabilities.indexOf(Math.max(...probabilities));
  $('temperature-explanation').textContent = temperature === 1
    ? `T = 1，分数除以1后保持原样。“${tokens[best]}”的分数最高，概率是${percentage(probabilities[best])}。试着把T调到0.3或2，比较长条的变化。`
    : `T = ${temperature}。“${tokens[best]}”的概率是${percentage(probabilities[best])}。${temperature < 1 ? '分数之间的差距被放大，高分词得到更多概率。' : '分数之间的差距被缩小，概率分配得更分散。'}`;
  const weights = scores.map(score => Math.exp(score / temperature));
  const sum = weights.reduce((a, b) => a + b, 0);
  $('calculation').innerHTML = `<p>温度先把“好”的分数变成 ${scores[0]} ÷ ${temperature} = <strong>${decimal(scores[0] / temperature)}</strong>。</p><p>再取指数：e<sup>${decimal(scores[0] / temperature)}</sup> ≈ <strong>${decimal(weights[0])}</strong>。e约等于2.718，指数运算把正分数、负分数都变成正数。</p><p>五个词都这样算，得到的五个正数相加，约为 <strong>${decimal(sum)}</strong>。</p><p>最后，“好”的概率 = ${decimal(weights[0])} ÷ ${decimal(sum)} ≈ <strong>${percentage(probabilities[0])}</strong>。其他四个词也除以同一个总和。</p>`;
  $('segments').innerHTML = finalProbabilities.map((p, i) => p > 0 ? `<span style="width:${p * 100}%;background:${colors[i]}"></span>` : '').join('');
  $('sampling-legend').innerHTML = tokens.map((token, i) => `<span${finalProbabilities[i] === 0 ? ' class="muted"' : ''}><i class="swatch" style="background:${colors[i]}"></i>${token} ${percentage(finalProbabilities[i])}</span>`).join('');
  $('lottery').setAttribute('aria-label', `0到1按抽样概率分段：${tokens.map((t, i) => `${t}占${percentage(finalProbabilities[i])}`).join('，')}`);
  $('k-field').hidden = mode !== 'top-k'; $('p-field').hidden = mode !== 'top-p';
  const ranked = probabilities.map((p, i) => ({ p, i })).sort((a, b) => b.p - a.p || a.i - b.i);
  const kept = ranked.filter(x => finalProbabilities[x.i] > 0);
  const mass = kept.reduce((sum, x) => sum + x.p, 0);
  $('filter-explanation').textContent = mode === 'all'
    ? '当前保留全部五个词。上面的Softmax概率，也就是下面抽词使用的概率。'
    : `${mode === 'top-k' ? `先保留概率最高的${topK}个词` : `从概率最高的词开始累加，达到${percentage(topP)}时停下`}：${kept.map(x => `“${tokens[x.i]}”`).join('、')}。它们原来的概率合计${percentage(mass)}，各自除以这个合计，得到下面抽词使用的新概率。`;
  renderSamples();
}

function updateDistribution() {
  renderDistribution();
  clearSamples('参数变了。下面按新的概率重新开始抽样。');
}

function draw() {
  const random = Math.random();
  const index = sampleIndex(finalProbabilities, random);
  counts[index] += 1; lastDraw = { index, random };
}

function showDraw() {
  const { index, random } = lastDraw;
  const lower = finalProbabilities.slice(0, index).reduce((a, b) => a + b, 0);
  const upper = lower + finalProbabilities[index];
  $('random-marker').hidden = false;
  $('random-marker').style.left = `${random * 100}%`;
  $('chosen-word').textContent = tokens[index];
  $('chosen-word').style.color = colors[index];
  $('draw-description').textContent = `这次随机数是${random.toFixed(4)}，落在“${tokens[index]}”的区间[${lower.toFixed(4)}, ${upper.toFixed(4)})里，所以选中“${tokens[index]}”。区间包括左端点，不包括右端点。`;
  renderSamples();
}

for (const id of ['temperature', 'temperature-number']) {
  $(id).addEventListener('input', event => {
    const value = event.target.valueAsNumber;
    if (!Number.isFinite(value) || value < 0.1 || value > 3) { $('input-error').textContent = '温度请填写0.1到3之间的数。画面保留上一组有效参数。'; return; }
    temperature = value; $(id === 'temperature' ? 'temperature-number' : 'temperature').value = value;
    $('input-error').textContent = ''; updateDistribution();
  });
}
document.querySelectorAll('[data-temperature]').forEach(button => button.addEventListener('click', () => {
  temperature = Number(button.dataset.temperature); $('temperature').value = temperature; $('temperature-number').value = temperature;
  $('input-error').textContent = ''; updateDistribution();
}));
scores.forEach((_, i) => $(`score-${i}`).addEventListener('input', event => {
  const value = event.target.valueAsNumber;
  if (!Number.isFinite(value) || value < -10 || value > 10) { $('input-error').textContent = '示例分数请填写−10到10之间的数。画面保留上一组有效分数。'; return; }
  scores[i] = value; $('input-error').textContent = ''; updateDistribution();
}));
$('filter-mode').addEventListener('change', event => { mode = event.target.value; updateDistribution(); });
for (const [id, check, set] of [
  ['top-k', v => Number.isInteger(v) && v >= 1 && v <= 5, v => { topK = v; }],
  ['top-p', v => Number.isFinite(v) && v >= 0.01 && v <= 1, v => { topP = v; }]
]) $(id).addEventListener('input', event => {
  const value = event.target.valueAsNumber;
  if (!check(value)) { $('input-error').textContent = id === 'top-k' ? 'k请填写1到5之间的整数。' : 'p请填写0.01到1之间的数。'; return; }
  set(value); $('input-error').textContent = ''; updateDistribution();
});
$('sample-once').addEventListener('click', () => { stopBatch(); draw(); showDraw(); });
$('sample-many').addEventListener('click', () => {
  if (animation !== null) { stopBatch(); return; }
  let remaining = 1000;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const tick = () => {
    for (let i = 0, size = Math.min(remaining, reducedMotion ? 1000 : 50); i < size; i++) { draw(); remaining -= 1; }
    showDraw();
    if (remaining > 0) { animation = requestAnimationFrame(tick); } else { animation = null; $('sample-many').textContent = '连续抽1000次'; }
  };
  $('sample-many').textContent = '暂停连续抽样';
  animation = requestAnimationFrame(tick);
});
$('clear-samples').addEventListener('click', () => clearSamples());
$('reset-example').addEventListener('click', () => {
  scores = [...original]; temperature = 1; mode = 'all'; topK = 3; topP = 0.9;
  scores.forEach((score, i) => { $(`score-${i}`).value = score; });
  $('temperature').value = 1; $('temperature-number').value = 1; $('filter-mode').value = mode; $('top-k').value = topK; $('top-p').value = topP;
  $('input-error').textContent = ''; updateDistribution();
});
document.addEventListener('visibilitychange', () => { if (document.hidden) stopBatch(); });
renderDistribution();
