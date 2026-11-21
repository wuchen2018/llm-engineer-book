export function softmax(scores, temperature = 1) {
  if (!scores.length || scores.some(x => !Number.isFinite(x))) throw new RangeError('分数须是有限数值');
  if (!Number.isFinite(temperature) || temperature <= 0) throw new RangeError('温度须大于0');
  const maximum = Math.max(...scores);
  const weights = scores.map(x => Math.exp((x - maximum) / temperature));
  const sum = weights.reduce((a, b) => a + b, 0);
  return weights.map(x => x / sum);
}

export function filterProbabilities(probabilities, mode = 'all', parameter = 1) {
  if (!probabilities.length || probabilities.some(p => !Number.isFinite(p) || p < 0) || probabilities.reduce((a, b) => a + b, 0) <= 0) throw new RangeError('概率无效');
  const ordered = probabilities.map((p, i) => ({ p, i })).sort((a, b) => b.p - a.p || a.i - b.i);
  let kept = ordered;
  if (mode === 'top-k') {
    if (!Number.isInteger(parameter) || parameter < 1 || parameter > probabilities.length) throw new RangeError('k无效');
    kept = ordered.slice(0, parameter);
  } else if (mode === 'top-p') {
    if (!Number.isFinite(parameter) || parameter <= 0 || parameter > 1) throw new RangeError('p无效');
    if (parameter === 1) return [...probabilities];
    kept = []; let total = 0;
    for (const item of ordered) { kept.push(item); total += item.p; if (total >= parameter - 1e-12) break; }
  } else if (mode !== 'all') throw new RangeError('筛选方式无效');
  const indices = new Set(kept.map(x => x.i));
  const total = kept.reduce((sum, x) => sum + x.p, 0);
  return probabilities.map((p, i) => indices.has(i) ? p / total : 0);
}

export function sampleIndex(probabilities, random = Math.random()) {
  if (!Number.isFinite(random) || random < 0 || random >= 1) throw new RangeError('随机数须在[0,1)中');
  const total = probabilities.reduce((a, b) => a + b, 0);
  if (!Number.isFinite(total) || total <= 0 || probabilities.some(p => p < 0 || !Number.isFinite(p))) throw new RangeError('概率无效');
  let cumulative = 0;
  for (let i = 0; i < probabilities.length; i++) {
    cumulative += probabilities[i] / total;
    if (random < cumulative && probabilities[i] > 0) return i;
  }
  return probabilities.findLastIndex(p => p > 0);
}
