#!/usr/bin/env node
// Offline verification; no API calls, translation services, or project data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

const root = path.resolve(__dirname, '..');
const web = path.join(root, 'apps/web');
const webRequire = createRequire(path.join(web, 'package.json'));
const { parse } = webRequire('@formatjs/icu-messageformat-parser');

function flatten(value, prefix = '', result = {}) {
  assert(value && typeof value === 'object' && !Array.isArray(value), `${prefix}: expected object`);
  for (const [key, child] of Object.entries(value)) {
    const id = prefix ? `${prefix}.${key}` : key;
    if (typeof child === 'string') result[id] = child;
    else flatten(child, id, result);
  }
  return result;
}

function signature(nodes) {
  return nodes.flatMap((node) => {
    if (node.type === 0) return [];
    if (node.type === 8) return [`tag:${node.value}:${JSON.stringify(signature(node.children))}`];
    if (node.options) {
      const options = Object.fromEntries(Object.keys(node.options).sort().map(
        (key) => [key, signature(node.options[key].value)],
      ));
      return [`${node.type}:${node.value}:${node.offset || 0}:${node.pluralType || ''}:${JSON.stringify(options)}`];
    }
    return [`${node.type}:${node.value || ''}:${JSON.stringify(node.style || null)}`];
  }).sort();
}

function checkPair(english, translated) {
  assert.deepEqual(signature(parse(translated)), signature(parse(english)), 'ICU arguments/tags/branches differ');
  const code = (text) => [...text.matchAll(/`([^`]+)`/g)].map((match) => match[0]).sort();
  assert.deepEqual(code(translated), code(english), 'Inline code differs');
}

function main() {
  // Positive and negative controls: a verifier that accepts broken placeholders is not useful.
  checkPair('Hello {name}', '你好，{name}');
  assert.throws(() => checkPair('Hello {name}', '你好'));
  assert.throws(() => checkPair('<b>Hello</b>', '你好'));
  assert.throws(() => checkPair('{n, plural, one {One} other {Many}}', '{n} 个'));
  assert.throws(() => checkPair('Use `GET /api`', '使用 `POST /api`'));

  const read = (locale) => flatten(JSON.parse(fs.readFileSync(path.join(web, 'messages', `${locale}.json`), 'utf8')));
  const en = read('en');
  const zh = read('zh');
  assert.deepEqual(Object.keys(zh).sort(), Object.keys(en).sort(), 'Missing or extra Chinese keys');
  let chineseEntries = 0;
  const errors = [];
  for (const [key, english] of Object.entries(en)) {
    try {
      assert(zh[key].trim().length > 0 || english.trim().length === 0, 'Empty translation');
      assert(!/[\uac00-\ud7af]/u.test(zh[key]), 'Unexpected Korean text in Chinese UI catalog');
      checkPair(english, zh[key]);
      if (/[\u3400-\u9fff]/u.test(zh[key])) chineseEntries += 1;
    } catch (error) {
      errors.push(`${key}: ${error.message}`);
    }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  for (const [key, value] of Object.entries({
    'settings.messagingPolicyHelper': '智能体',
    'presence.panelTitle': '团队状态',
    'recruiter.title': '接入智能体',
    'board.storyPoints': '工作量点数',
    'activityLog.filterActor': '操作者',
  })) assert(zh[key].includes(value), `${key}: LD terminology regressed`);
  console.log(JSON.stringify({ keys: Object.keys(en).length, chineseEntries, errors: 0, offline: true }));
}

if (require.main === module) main();
module.exports = { flatten, signature, checkPair };
